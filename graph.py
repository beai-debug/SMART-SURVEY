"""
graph.py
LangChain OpenAI (GPT-5) + LangGraph orchestration.
"""

import os
import json
import time
import traceback
from typing import TypedDict, Optional, Any
from dotenv import load_dotenv

# FIXED IMPORT — new LC version
from langchain_openai import ChatOpenAI

from langchain_core.messages import SystemMessage, HumanMessage

from langgraph.graph import StateGraph, END

from smart_survey_engine import (
    build_schema,
    build_summary_prompt,
    combine_rows_to_single,
    exec_pandas_expression,
    plot_from_df
)

# -------------------------
# ENV
# -------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5")
CSV_PATH = os.getenv("CSV_PATH", "school_survey.csv")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing in .env")

# -------------------------
# GPT-5 LANGCHAIN CLIENT
# -------------------------
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=0.1,
    max_tokens=1500,
    api_key=OPENAI_API_KEY
)

def llm_call(system_prompt: str, user_prompt: str):
    try:
        resp = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        content = resp.content if resp.content else ""
        if not content:
            print(f"WARNING: LLM returned empty content. Response: {resp}")
        return content
    except Exception as e:
        print("LLM ERROR:", e)
        print(f"Model: {MODEL_NAME}")
        traceback.print_exc()
        raise

# -------------------------
# LANGGRAPH STATE
# -------------------------
class SurveyState(TypedDict, total=False):
    user_query: str
    user_questions: Optional[list]
    llm_raw: str
    pandas_expression: str
    plot_spec: Optional[dict]
    selected_df: Any
    plot_paths: Optional[list]
    summary: Optional[str]


# -------------------------
# NODE: GENERATE QUERY
# -------------------------
def node_generate_query(state: SurveyState):
    schema = build_schema(CSV_PATH)
    
    # Extract column names for clearer instruction
    column_names = list(schema.get("columns", {}).keys())

    system_text = """You are a pandas query generator. You produce ONLY valid Python pandas expressions.

CRITICAL RULES FOR COLUMN NAMES:
- Column names contain spaces and special characters (like '?', ',')
- ALWAYS use bracket notation with string keys: df['Column Name']
- NEVER use dot notation (df.Column is WRONG)
- For filtering, use: df[df['Column Name'] == 'value']
- For multiple conditions, use: df[(df['Col1'] == 'val1') & (df['Col2'] == 'val2')]

EXAMPLES OF CORRECT SYNTAX:
- df[df['Your class'] == '12th']
- df[df['Your class'].isin(['10 th', '11th', '12th'])]
- df[(df['Your class'] == '12th') & (df['How much time do you spend every day on your self study and homework?'] == '<2 Hrs')]
- df[df['Subject group'] == 'IT/CS']

IMPORTANT VALUE NOTES:
- Class values: '6 th', '7 th', '8 th', '9 th', '10 th', '11th', '12th' (note the spacing inconsistency)
- Study time: '<2 Hrs', '2-3 Hrs', '3-4 Hrs', 'More than 4 Hrs'
- Use EXACT values from the schema's top_values

Return EITHER:
1) A pandas expression starting with df... that returns a DataFrame
2) A JSON object: {"pandas_expression": "df[...]", "plot_spec": {"chart_type": "count", "column": "..."}}

NO markdown, NO explanation, NO code blocks - just the expression or JSON."""

    user_text = (
        "AVAILABLE COLUMNS:\n" + json.dumps(column_names, indent=2) +
        "\n\nFULL SCHEMA WITH VALUES:\n" + json.dumps(schema, indent=2, ensure_ascii=False) +
        "\n\nUSER QUERY: " + str(state.get("user_query", "")) +
        "\n\nGenerate a valid pandas expression to answer this query."
    )

    raw = llm_call(system_text, user_text)
    state["llm_raw"] = raw

    # Initialize to None
    pandas_expr = None
    plot_spec = None

    # Strip markdown code blocks if present
    cleaned_raw = raw.strip()
    
    # Handle various markdown formats
    for prefix in ["```python", "```json", "```"]:
        if cleaned_raw.startswith(prefix):
            cleaned_raw = cleaned_raw[len(prefix):]
            break
    
    if cleaned_raw.endswith("```"):
        cleaned_raw = cleaned_raw[:-3]
    
    cleaned_raw = cleaned_raw.strip()

    # Try to parse as JSON first
    try:
        parsed = json.loads(cleaned_raw)
        pandas_expr = parsed.get("pandas_expression", "")
        plot_spec = parsed.get("plot_spec")
    except json.JSONDecodeError:
        # Not JSON, treat as raw pandas expression
        pandas_expr = cleaned_raw
        plot_spec = None

    # Clean and validate
    if pandas_expr:
        pandas_expr = pandas_expr.strip()
        # Remove any remaining markdown artifacts
        if pandas_expr.startswith("```"):
            pandas_expr = pandas_expr.split("\n", 1)[-1] if "\n" in pandas_expr else pandas_expr[3:]
        if pandas_expr.endswith("```"):
            pandas_expr = pandas_expr[:-3]
        pandas_expr = pandas_expr.strip()
    
    # Ensure pandas_expression is never None or empty
    if not pandas_expr:
        raise ValueError(f"LLM did not return a valid pandas expression. Raw response: '{raw}'")
    
    # Ensure it starts with df
    if not pandas_expr.startswith("df"):
        raise ValueError(f"Expression must start with 'df'. Got: '{pandas_expr}'")

    # Return dict to update state
    return {
        "pandas_expression": pandas_expr,
        "plot_spec": plot_spec,
        "llm_raw": raw,
        "user_query": state.get("user_query"),
        "user_questions": state.get("user_questions")
    }



# -------------------------
# NODE: EXECUTE + 5 RETRIES
# -------------------------
def node_execute_with_retry(state: SurveyState):
    expr = state.get("pandas_expression")
    
    if not expr:
        raise ValueError(f"No pandas expression found in state. State keys: {list(state.keys())}. The query generation step may have failed.")
    
    # Get schema for fix prompts
    schema = build_schema(CSV_PATH)
    column_names = list(schema.get("columns", {}).keys())

    for attempt in range(1, 6):
        try:
            df_sel = exec_pandas_expression(CSV_PATH, expr)
            state["selected_df"] = df_sel
            return state
        except Exception as e:
            err = str(e)
            print(f"\n[Attempt {attempt}/5] Error running pandas expression:\n{err}")

            # Ask LLM to fix with detailed guidance
            fix_sys = """You fix pandas expressions. Output ONLY valid Python code starting with df.

CRITICAL RULES:
- Use bracket notation: df['Column Name'] NOT df.Column
- Column names have spaces and special characters
- For filtering: df[df['Column'] == 'value']
- Multiple conditions: df[(df['Col1'] == 'val1') & (df['Col2'] == 'val2')]
- Class values: '6 th', '7 th', '8 th', '9 th', '10 th', '11th', '12th'
- Study time: '<2 Hrs', '2-3 Hrs', '3-4 Hrs', 'More than 4 Hrs'

NO markdown, NO explanation, NO code blocks - ONLY the pandas expression."""

            fix_user = f"""AVAILABLE COLUMNS:
{json.dumps(column_names, indent=2)}

FAILED EXPRESSION:
{expr}

ERROR:
{err}

Return ONLY the corrected pandas expression."""

            raw_fix = llm_call(fix_sys, fix_user).strip()
            
            # Clean markdown from fix response
            if raw_fix.startswith("```python"):
                raw_fix = raw_fix[9:]
            elif raw_fix.startswith("```"):
                raw_fix = raw_fix[3:]
            if raw_fix.endswith("```"):
                raw_fix = raw_fix[:-3]
            
            expr = raw_fix.strip()
            state["pandas_expression"] = expr
            time.sleep(1)

    raise RuntimeError("❌ All 5 pandas execution retries failed.")


# -------------------------
# NODE: PLOT
# -------------------------
def node_plot(state: SurveyState):
    if state.get("plot_spec"):
        try:
            paths = plot_from_df(state["selected_df"], state["plot_spec"])
            state["plot_paths"] = paths
        except Exception as e:
            print("Plot error:", e)
            state["plot_paths"] = None
    else:
        state["plot_paths"] = None
    return state


# -------------------------
# NODE: SUMMARY (GPT-5)
# -------------------------
def node_summary(state: SurveyState):
    df = state.get("selected_df")
    if df is None:
        state["summary"] = None
        return state

    combined = combine_rows_to_single(df)
    schema = build_schema(CSV_PATH)
    summary_prompt = build_summary_prompt(schema, combined)

    sys = "You summarize selected survey rows. Output JSON only."

    summary = llm_call(sys, summary_prompt)
    state["summary"] = summary
    return state


# -------------------------
# BUILD GRAPH
# -------------------------
graph = StateGraph(SurveyState)

graph.add_node("generate_query", node_generate_query)
graph.add_node("execute_query", node_execute_with_retry)
graph.add_node("plot", node_plot)
graph.add_node("summary", node_summary)

graph.set_entry_point("generate_query")
graph.add_edge("generate_query", "execute_query")
graph.add_edge("execute_query", "plot")
graph.add_edge("plot", "summary")
graph.add_edge("summary", END)

flow = graph.compile()


# -------------------------
# ENTRYPOINT FUNCTION
# -------------------------
def run_survey_query(user_query: str, user_questions=None):
    state = SurveyState()
    state["user_query"] = user_query
    state["user_questions"] = user_questions
    return flow.invoke(state)

# -------------------------
# TEST
# -------------------------
if __name__ == "__main__":
    out = run_survey_query(
        "Show me 12th class students with '<2 Hrs' study time and plot subject group count.",
        ["Top issues?", "3 recommendations?"]
    )

    print("\n=== FINAL EXPRESSION ===\n", out.get("pandas_expression"))
    print("\n=== PLOT ===\n", out.get("plot_paths"))
    print("\n=== SUMMARY ===\n", out.get("summary"))
