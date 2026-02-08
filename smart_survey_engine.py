"""
smart_survey_engine.py

Utilities for:
 - building dataset schema (with form enums)
 - executing pandas expressions (using exec)
 - generating Seaborn + Plotly plots
 - combining selected rows to a single aggregated "row" summary

WARNING: exec() is used per user's request. This file includes basic guarding but is NOT a production sandbox.
If you will run untrusted input, run this inside a hardened container or implement an AST-based allowlist parser.
"""

import os
import json
import datetime
from typing import Dict, Any
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

OUTPUT_DIR = "smart_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------
# ALL POSSIBLE GOOGLE FORM VALUES (ENUMS)
# -------------------------
FORM_ENUMS = {
    "classes": ["6 th", "7 th", "8 th", "9 th", "10 th", "11th", "12th"],
    "study_time": ["<2 Hrs", "2-3 Hrs", "3-4 Hrs", "More than 4 Hrs"],
    "subject_groups": ["Maths", "Biology", "IT/CS", "Commerce", "Not Applicable"],
    "subjects_all": [
        "Hindi","English","Maths","Science","Social Science","Physics","Chemistry",
        "Biology","IT/CS","Business Studies","Accountancy","Economics","Other"
    ],
    "teacher_support_scale": ["Strongly agree","Agree","Neutral","Disagree","Strongly disagree"],
    "real_world_scale": ["Excellent","Good","Average","Poor","Very poor"],
    "labs_scale": ["Strongly agree","Agree","Neutral","Disagree","Strongly disagree"],
    "extracurricular_scale": ["Very sufficient","Sufficient","Neutral","Insufficient","Very insufficient"],
    "events_scale": ["Strongly agree","Agree","Neutral","Disagree","Strongly disagree"],
    "transport_scale": ["Very satisfied","Satisfied","Neutral","Dissatisfied","Very dissatisfied"],
    "career_scale": ["Strongly agree","Agree","Neutral","Disagree","Strongly disagree"],
    "bullying_scale": ["Very well","Well","Adequately","Poorly","Very poorly"],
    "fee_behaviour": ["Strongly positive","Positive","Neutral","Negative","Strongly negative"],
    "exam_scale": ["Strongly agree","Agree","Neutral","Disagree","Strongly disagree"],
    "stress_scale": ["Very well","Well","Adequately","Poorly","Very poorly"],
    "competitive_scale": ["Strongly agree","Agree","Neutral","Disagree","Strongly disagree"],
    "teaching_quality": ["Highly satisfied","Satisfied","Somewhat satisfied","Not satisfied","Extremely dissatisfied"],
    "recommend_scale": ["1","2","3","4","5"]
}

# -------------------------
# Schema builder
# -------------------------
def build_schema(csv_path: str, top_n: int = 10) -> Dict[str, Any]:
    """
    Read CSV and build a JSON-like schema with dtypes and top values for domain guidance.
    """
    df = pd.read_csv(csv_path)
    schema = {"metadata": {"rows": int(len(df)), "columns": int(len(df.columns)), "generated_at": datetime.datetime.utcnow().isoformat() + "Z"},
              "columns": {}, "enums": FORM_ENUMS}
    for col in df.columns:
        ser = df[col].dropna()
        dtype = "numeric" if pd.api.types.is_numeric_dtype(ser) else ("datetime" if pd.api.types.is_datetime64_any_dtype(ser) else "string")
        top_values = ser.astype(str).value_counts().head(top_n).index.tolist()
        sample = ser.astype(str).drop_duplicates().head(3).tolist()
        schema["columns"][col] = {"dtype": dtype, "n_unique": int(ser.nunique()) if len(ser)>0 else 0,
                                 "top_values": top_values, "sample_values": sample}
    return schema


# -------------------------
# Exec runner (exec)
# -------------------------
def exec_pandas_expression(csv_path: str, expression: str, max_rows: int = 1000) -> pd.DataFrame:
    """
    Execute a pandas expression using exec().
    expression must be a Python expression that returns a pandas DataFrame when executed with 'df'.
    Example: "df[df['Your class'] == '10 th']"

    Basic safety: remove builtins. Still not perfectly safe for untrusted input.
    """
    df = pd.read_csv(csv_path)
    
    # Normalize column names - strip whitespace
    df.columns = df.columns.str.strip()
    
    # provide safe locals
    safe_locals = {"df": df, "pd": pd, "np": np}
    safe_globals = {"__builtins__": None}
    
    # Clean up the expression
    expression = expression.strip()
    
    # Remove any markdown code formatting if present
    if expression.startswith("```python"):
        expression = expression[9:]
    elif expression.startswith("```"):
        expression = expression[3:]
    if expression.endswith("```"):
        expression = expression[:-3]
    expression = expression.strip()
    
    code = "result = " + expression
    try:
        exec(code, safe_globals, safe_locals)
        result = safe_locals.get("result", None)
        if isinstance(result, pd.DataFrame):
            return result.head(max_rows).copy()
        elif isinstance(result, pd.Series):
            # Convert Series to DataFrame
            return result.to_frame().head(max_rows).copy()
        else:
            raise ValueError(f"Expression did not return a pandas DataFrame. Got type: {type(result)}")
    except Exception as e:
        raise RuntimeError(f"Error executing pandas expression: {e}\nExpression was: {expression}")


# -------------------------
# Plotting: seaborn + plotly
# -------------------------
def plot_from_df(df: pd.DataFrame, plot_spec: Dict[str, Any], output_dir: str = OUTPUT_DIR) -> Dict[str, str]:
    """
    plot_spec examples:
      {"chart_type": "count", "column": "Your class"}
      {"chart_type": "bar", "x": "Your class", "y": "How much time...", "agg":"count"}
      {"chart_type": "hist", "column": "What was your last year overall percentage or CGPA?", "bins": 10}
      {"chart_type": "scatter", "x": "col1", "y": "col2"}
    Returns dict with paths to produced files.
    """
    chart_type = plot_spec.get("chart_type", "").lower()
    out = {}
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Validate columns
    def ensure_col(c):
        if c and c not in df.columns:
            raise ValueError(f"Column '{c}' not in DataFrame")

    ensure_col(plot_spec.get("x"))
    ensure_col(plot_spec.get("y"))
    ensure_col(plot_spec.get("column"))

    # static seaborn + interactive plotly
    if chart_type in ("count",):
        col = plot_spec["column"]
        plt.figure(figsize=(10,6))
        order = df[col].value_counts().index
        sns.countplot(y=col, data=df, order=order)
        # Sanitize column name for filename
        safe_col = col.replace("/", "_").replace("?", "").replace(" ", "_")[:30]
        png = os.path.join(output_dir, f"count_{safe_col}_{timestamp}.png")
        plt.tight_layout(); plt.savefig(png); plt.close()
        out["seaborn_png"] = png

        # plotly - use proper column naming to avoid duplicates
        vc = df[col].value_counts().reset_index()
        vc.columns = ['category', 'count']  # Rename to avoid duplicate column issues
        fig = px.bar(vc, x="count", y="category", orientation='h', title=f"Count: {col}")
        fig.update_yaxes(title=col)
        html = os.path.join(output_dir, f"count_{safe_col}_{timestamp}.html")
        fig.write_html(html); out["plotly_html"] = html

    elif chart_type == "hist":
        col = plot_spec["column"]
        bins = plot_spec.get("bins", 10)
        plt.figure(figsize=(10,6))
        sns.histplot(pd.to_numeric(df[col], errors='coerce').dropna(), bins=bins)
        png = os.path.join(output_dir, f"hist_{col}_{timestamp}.png")
        plt.tight_layout(); plt.savefig(png); plt.close()
        out["seaborn_png"] = png

        fig = px.histogram(df, x=col, nbins=bins, title=f"Histogram: {col}")
        html = os.path.join(output_dir, f"hist_{col}_{timestamp}.html")
        fig.write_html(html); out["plotly_html"] = html

    elif chart_type in ("scatter", "line"):
        x = plot_spec["x"]; y = plot_spec["y"]
        plt.figure(figsize=(10,6))
        sns.scatterplot(data=df, x=x, y=y)
        png = os.path.join(output_dir, f"{chart_type}_{x}_{y}_{timestamp}.png")
        plt.tight_layout(); plt.savefig(png); plt.close()
        out["seaborn_png"] = png

        fig = px.scatter(df, x=x, y=y, title=f"{chart_type.title()}: {y} vs {x}")
        html = os.path.join(output_dir, f"{chart_type}_{x}_{y}_{timestamp}.html")
        fig.write_html(html); out["plotly_html"] = html

    elif chart_type in ("box", "violin"):
        x = plot_spec["x"]; y = plot_spec["y"]
        plt.figure(figsize=(10,6))
        if chart_type == "box":
            sns.boxplot(x=x, y=y, data=df)
        else:
            sns.violinplot(x=x, y=y, data=df)
        png = os.path.join(output_dir, f"{chart_type}_{x}_{y}_{timestamp}.png")
        plt.tight_layout(); plt.savefig(png); plt.close()
        out["seaborn_png"] = png

        fig = px.box(df, x=x, y=y, title=f"{chart_type.title()}: {y} by {x}")
        html = os.path.join(output_dir, f"{chart_type}_{x}_{y}_{timestamp}.html")
        fig.write_html(html); out["plotly_html"] = html

    elif chart_type == "heatmap":
        numeric = df.select_dtypes(include=[np.number]).corr()
        plt.figure(figsize=(10,8))
        sns.heatmap(numeric, annot=True, fmt=".2f")
        png = os.path.join(output_dir, f"heatmap_{timestamp}.png")
        plt.tight_layout(); plt.savefig(png); plt.close()
        out["seaborn_png"] = png

    else:
        raise ValueError(f"Unsupported chart_type: {chart_type}")

    return out


# -------------------------
# Combine selected rows into single aggregated dict
# -------------------------
def combine_rows_to_single(df_selected: pd.DataFrame) -> Dict[str, Any]:
    combined = {}
    for col in df_selected.columns:
        ser = df_selected[col].dropna()
        if ser.empty:
            combined[col] = None
            continue
        # numeric?
        numeric = pd.to_numeric(ser, errors='coerce').dropna()
        if len(numeric) > 0:
            combined[col] = {"type": "numeric", "count": int(len(ser)), "mean": float(numeric.mean()),
                             "median": float(numeric.median()), "min": float(numeric.min()), "max": float(numeric.max())}
            continue
        # categorical/text
        combined[col] = {"type": "categorical", "count": int(len(ser)), "unique": int(ser.nunique()),
                         "top_values": ser.astype(str).value_counts().head(5).to_dict(),
                         "sample": ser.astype(str).drop_duplicates().head(3).tolist()}
    return combined


# -------------------------
# Summary prompt builder to send to LLM
# -------------------------
def build_summary_prompt(schema: Dict[str, Any], combined_row: Dict[str, Any], user_questions=None) -> str:
    prompt = (
        "You are given an aggregated survey data summary (one combined row). "
        "Schema and enums are provided. Produce a concise, actionable JSON summary for school admins.\n\n"
        "Schema:\n" + json.dumps(schema, indent=2, ensure_ascii=False) +
        "\n\nCombined aggregated row:\n" + json.dumps(combined_row, indent=2, ensure_ascii=False)
    )
    if user_questions:
        prompt += "\n\nUser questions:\n" + "\n".join(f"- {q}" for q in user_questions)
    prompt += (
        "\n\nOutput MUST be a JSON object with keys: findings (list), recommendations (list), anomalies (list), next_checks (list), short_summary (string).\n"
        "Keep items short and prioritized."
    )
    return prompt
