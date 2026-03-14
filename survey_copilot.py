"""
survey_copilot.py
AI Analytics Copilot for School Survey Data
Combines SQL analytics (QUANT) + Semantic Search with pgvector (QUAL)
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from openai import OpenAI
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

load_dotenv()

# Database configuration - use environment variables
DB_CONFIG = {
    "database": os.getenv("DB_NAME", "smart_survey"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432"))
}

# OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
client = OpenAI(api_key=OPENAI_API_KEY)

# ═══════════════════════════════════════════════════════════════════════════════
# SENTIMENT GROUPING RULES
# ═══════════════════════════════════════════════════════════════════════════════

SENTIMENT_GROUPS = {
    "positive": [
        "Strongly agree", "Agree", "Highly satisfied", "Satisfied",
        "Very satisfied", "Excellent", "Very Good", "Good", "Very well", "Well",
        "Very sufficient", "Sufficient", "Strongly positive", "Positive"
    ],
    "neutral": [
        "Neutral", "Somewhat satisfied", "Average", "Adequately"
    ],
    "negative": [
        "Disagree", "Strongly disagree", "Dissatisfied", "Very dissatisfied",
        "Not satisfied", "Extremely dissatisfied", "Poor", "Very poor",
        "Poorly", "Very poorly", "Insufficient", "Very insufficient",
        "Negative", "Strongly negative"
    ]
}

# Database schema reference for LLM
DB_SCHEMA = """
Table: survey
Columns:
- id (SERIAL PRIMARY KEY)
- timestamp (TIMESTAMP)
- student_name (TEXT)
- school_name (TEXT)
- class (TEXT) -- values: '6 th', '7 th', '8 th', '9 th', '10 th', '11th', '12th'
- last_year_percentage (NUMERIC)
- study_time (TEXT) -- values: '<2 Hrs', '2-3 Hrs', '3-4 Hrs', 'More than 4 Hrs'
- toughest_subject (TEXT)
- subject_group (TEXT) -- values: 'Maths', 'Biology', 'IT/CS', 'Commerce', 'Not Applicable'

Satisfaction columns (all TEXT with Likert scales):
- teacher_support -- 'Strongly agree', 'Agree', 'Neutral', 'Disagree', 'Strongly disagree'
- real_world_examples -- 'Excellent', 'Good', 'Average', 'Poor', 'Very poor'
- interactive_classroom -- same as teacher_support
- lab_satisfaction -- same as teacher_support
- extracurricular_resources -- 'Very sufficient', 'Sufficient', 'Neutral', 'Insufficient', 'Very insufficient'
- school_events -- same as teacher_support
- transport_satisfaction -- 'Very satisfied', 'Satisfied', 'Neutral', 'Dissatisfied', 'Very dissatisfied'
- career_guidance -- same as teacher_support
- bullying_resolution -- 'Very well', 'Well', 'Adequately', 'Poorly', 'Very poorly'
- fee_behaviour -- 'Strongly positive', 'Positive', 'Neutral', 'Negative', 'Strongly negative'
- exam_fairness -- same as teacher_support
- wellness_support -- 'Very well', 'Well', 'Adequately', 'Poorly', 'Very poorly'
- competitive_exam_preparedness -- same as teacher_support
- overall_teaching_satisfaction -- 'Highly satisfied', 'Satisfied', 'Somewhat satisfied', 'Not satisfied', 'Extremely dissatisfied'
- recommendation_score (INTEGER) -- 1 to 5

Open-ended feedback columns:
- teacher_feedback (TEXT)
- school_feedback (TEXT)
- school_suggestions (TEXT)

Vector columns (for semantic search):
- teacher_feedback_embedding (vector(1536))
- school_feedback_embedding (vector(1536))
- school_suggestions_embedding (vector(1536))
"""


# Output directory for charts
OUTPUT_DIR = Path("smart_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Set seaborn style for beautiful charts
sns.set_theme(style="whitegrid", palette="husl")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11


def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)


def generate_chart(results: List[Dict], query: str, chart_type: str = "auto") -> Optional[str]:
    """
    Generate a beautiful chart from query results and save to output folder
    Returns the path to the saved chart
    """
    if not results:
        return None
    
    try:
        df = pd.DataFrame(results)
        
        # Convert Decimal to float for plotting
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
                except:
                    pass
        
        # Determine chart type based on data structure
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # Create timestamp for unique filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Determine the best chart type
        fig, ax = plt.subplots(figsize=(12, 7))
        
        if len(categorical_cols) >= 2 and 'percentage' in [c.lower() for c in numeric_cols]:
            # Grouped bar chart for distributions
            pct_col = [c for c in numeric_cols if 'percentage' in c.lower() or 'pct' in c.lower()][0] if any('percentage' in c.lower() or 'pct' in c.lower() for c in numeric_cols) else numeric_cols[0]
            
            # Create pivot if we have two categorical columns
            cat1, cat2 = categorical_cols[0], categorical_cols[1]
            
            try:
                pivot_df = df.pivot(index=cat1, columns=cat2, values=pct_col).fillna(0)
                pivot_df.plot(kind='bar', ax=ax, colormap='husl', width=0.8, edgecolor='white')
                ax.set_xlabel(cat1.replace('_', ' ').title())
                ax.set_ylabel('Percentage (%)')
                ax.legend(title=cat2.replace('_', ' ').title(), bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.xticks(rotation=45, ha='right')
            except:
                # Fallback to simple bar
                if pct_col in df.columns:
                    sns.barplot(data=df, x=cat1, y=pct_col, hue=cat2 if len(categorical_cols) > 1 else None, ax=ax, palette='husl')
                    plt.xticks(rotation=45, ha='right')
        
        elif len(categorical_cols) == 1 and len(numeric_cols) >= 1:
            # Simple bar chart
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Sort by value for better visualization
            df_sorted = df.sort_values(num_col, ascending=True)
            
            colors = sns.color_palette('husl', len(df_sorted))
            bars = ax.barh(df_sorted[cat_col].astype(str), df_sorted[num_col], color=colors, edgecolor='white')
            
            # Add value labels
            for bar, val in zip(bars, df_sorted[num_col]):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                       f'{val:.1f}%' if 'percent' in num_col.lower() else f'{val:.0f}',
                       va='center', fontsize=10)
            
            ax.set_xlabel(num_col.replace('_', ' ').title())
            ax.set_ylabel(cat_col.replace('_', ' ').title())
        
        elif len(numeric_cols) >= 2:
            # Scatter or line chart
            sns.scatterplot(data=df, x=numeric_cols[0], y=numeric_cols[1], ax=ax, s=100, palette='husl')
        
        else:
            # Fallback: simple count bar chart
            if categorical_cols:
                df[categorical_cols[0]].value_counts().plot(kind='bar', ax=ax, color=sns.color_palette('husl'))
                plt.xticks(rotation=45, ha='right')
        
        # Style the chart
        ax.set_title(f"📊 {query[:60]}{'...' if len(query) > 60 else ''}", fontsize=14, fontweight='bold', pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        # Save chart - replace spaces with underscores for URL-safe filenames
        safe_query = "".join(c if c.isalnum() or c in '_-' else '_' for c in query[:30])
        filename = f"chart_{safe_query}_{timestamp}.png"
        filepath = OUTPUT_DIR / filename
        
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
        return str(filepath)
    
    except Exception as e:
        print(f"Chart generation error: {e}")
        plt.close()
        return None


def llm_call(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """Call OpenAI LLM"""
    try:
        kwargs = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        raise


def generate_query_embedding(text: str) -> List[float]:
    """Generate embedding for a search query"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: INTENT ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

def classify_intent(query: str) -> str:
    """
    Classify query intent as QUANT, QUAL, or MIXED
    """
    system_prompt = """You are an intent classifier for a school survey analytics system.
    
Classify the user query into exactly ONE of these categories:

QUANT - Query needs numbers, percentages, distributions, comparisons, trends, counts, averages.
Examples: "average satisfaction", "% dissatisfied", "compare classes", "how many students"

QUAL - Query needs opinions, complaints, suggestions, feedback themes, reasons.
Examples: "what students complain about", "common issues", "feedback summary", "suggestions"

MIXED - Query needs BOTH metrics AND explanations/reasons.
Examples: "why dissatisfaction is high", "reasons behind low scores", "explain the trends"

Respond with ONLY one word: QUANT, QUAL, or MIXED"""

    response = llm_call(system_prompt, f"Query: {query}")
    intent = response.strip().upper()
    
    if intent not in ["QUANT", "QUAL", "MIXED"]:
        # Default to QUANT if unclear
        return "QUANT"
    
    return intent


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: QUANTITATIVE EXECUTION (SQL)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_sql(query: str, additional_context: str = "") -> str:
    """Generate SQL query from natural language"""
    system_prompt = f"""You are a PostgreSQL SQL generator for survey analytics.

DATABASE SCHEMA:
{DB_SCHEMA}

RULES:
1. Generate ONLY valid PostgreSQL SQL
2. ALWAYS include COUNT(*) for sample sizes
3. Use GROUP BY for distributions
4. Calculate percentages using: ROUND(COUNT(*)::numeric * 100 / SUM(COUNT(*)) OVER (), 1)
5. For sentiment analysis, group values as:
   - POSITIVE: 'Strongly agree', 'Agree', 'Highly satisfied', 'Satisfied', 'Very satisfied', 'Excellent', 'Very Good', 'Good', 'Very well', 'Well', 'Very sufficient', 'Sufficient', 'Strongly positive', 'Positive'
   - NEUTRAL: 'Neutral', 'Somewhat satisfied', 'Average', 'Adequately'
   - NEGATIVE: 'Disagree', 'Strongly disagree', 'Dissatisfied', 'Very dissatisfied', 'Not satisfied', 'Extremely dissatisfied', 'Poor', 'Very poor', 'Poorly', 'Very poorly', 'Insufficient', 'Very insufficient', 'Negative', 'Strongly negative'
6. Never use SELECT * - always specify columns
7. Always alias computed columns meaningfully
8. Class values have spaces: '6 th', '7 th', etc. (except '11th', '12th')

{additional_context}

Return ONLY the SQL query, no explanation."""

    response = llm_call(system_prompt, f"Generate SQL for: {query}")
    
    # Clean response
    sql = response.strip()
    if sql.startswith("```sql"):
        sql = sql[6:]
    elif sql.startswith("```"):
        sql = sql[3:]
    if sql.endswith("```"):
        sql = sql[:-3]
    
    return sql.strip()


def execute_sql(sql: str) -> Tuple[List[Dict], int]:
    """Execute SQL and return results with sample size"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute(sql)
        results = [dict(row) for row in cur.fetchall()]
        
        # Calculate sample size from results or run count query
        sample_size = 0
        if results:
            # Try to find count column
            for row in results:
                for key, val in row.items():
                    if 'count' in key.lower() and isinstance(val, (int, float)):
                        sample_size += int(val)
            
            # If no count found, run separate count
            if sample_size == 0:
                cur.execute("SELECT COUNT(*) as total FROM survey")
                sample_size = cur.fetchone()['total']
        
        return results, sample_size
    
    except Exception as e:
        raise RuntimeError(f"SQL Error: {e}\nQuery: {sql}")
    finally:
        cur.close()
        conn.close()


def run_quant_analysis(query: str, filters: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Run quantitative analysis using SQL
    Returns structured results with sample size and metrics
    """
    # Generate SQL
    additional_context = ""
    if filters:
        additional_context = f"Apply these filters: {json.dumps(filters)}"
    
    sql = generate_sql(query, additional_context)
    
    # Execute with retry on failure
    for attempt in range(3):
        try:
            results, sample_size = execute_sql(sql)
            
            return {
                "success": True,
                "sample_size": sample_size,
                "results": results,
                "sql": sql,
                "warning": "⚠️ Sample size < 10, insights may be unreliable" if sample_size < 10 else None
            }
        
        except Exception as e:
            if attempt < 2:
                # Ask LLM to fix the SQL
                fix_prompt = f"Fix this SQL error:\n\nSQL: {sql}\n\nError: {str(e)}\n\nReturn only the corrected SQL."
                sql = llm_call("You fix SQL syntax errors. Return only valid PostgreSQL.", fix_prompt)
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "sql": sql
                }


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: QUALITATIVE EXECUTION (pgvector Semantic Search)
# ═══════════════════════════════════════════════════════════════════════════════

def run_semantic_search(
    query: str,
    feedback_column: str = "teacher_feedback",
    filters: Optional[Dict] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Run semantic similarity search using pgvector
    IMPROVED: Now fetches FULL database rows using roll_number + school_name as keys
    """
    # Determine embedding column
    embedding_map = {
        "teacher_feedback": "teacher_feedback_embedding",
        "school_feedback": "school_feedback_embedding",
        "school_suggestions": "school_suggestions_embedding"
    }
    
    embedding_col = embedding_map.get(feedback_column, "teacher_feedback_embedding")
    
    # Generate query embedding
    query_embedding = generate_query_embedding(query)
    
    # Build SQL with filters
    filter_clauses = [f"{embedding_col} IS NOT NULL"]
    
    if filters:
        if "class" in filters:
            filter_clauses.append(f"class = '{filters['class']}'")
        if "subject_group" in filters:
            filter_clauses.append(f"subject_group = '{filters['subject_group']}'")
        if "dissatisfied" in filters and filters["dissatisfied"]:
            # Filter for negative sentiment
            negative_values = "', '".join(SENTIMENT_GROUPS["negative"])
            filter_clauses.append(f"""(
                overall_teaching_satisfaction IN ('{negative_values}')
                OR transport_satisfaction IN ('{negative_values}')
                OR lab_satisfaction IN ('Disagree', 'Strongly disagree')
            )""")
    
    where_clause = " AND ".join(filter_clauses)
    
    # STEP 1: Vector similarity search - get roll_number + school_name + similarity scores
    similarity_sql = f"""
    SELECT 
        roll_number,
        school_name,
        ROUND((1 - ({embedding_col} <=> %s::vector))::numeric, 4) as similarity
    FROM survey
    WHERE {where_clause}
    ORDER BY {embedding_col} <=> %s::vector
    LIMIT {limit}
    """
    
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get similar records with their keys and scores
        cur.execute(similarity_sql, (query_embedding, query_embedding))
        similarity_results = [dict(row) for row in cur.fetchall()]
        
        if not similarity_results:
            return {
                "success": True,
                "count": 0,
                "feedback": [],
                "full_rows": [],
                "warning": "No relevant feedback found"
            }
        
        # STEP 2: Fetch FULL rows from actual database using roll_number + school_name
        roll_school_pairs = [(r['roll_number'], r['school_name'], r['similarity']) 
                             for r in similarity_results]
        
        # Build query to fetch complete rows
        fetch_full_sql = """
        SELECT 
            id, timestamp, student_name, roll_number, school_name, class,
            last_year_percentage, study_time, toughest_subject, subject_group,
            teacher_rating_excellent, teacher_rating_very_good, teacher_rating_good,
            teacher_rating_average, teacher_rating_poor,
            teacher_support, learning_goal_method, real_world_examples, interactive_classroom,
            lab_satisfaction, extracurricular_resources, school_events,
            transport_satisfaction, career_guidance, bullying_resolution, fee_behaviour,
            exam_fairness, wellness_support, competitive_exam_preparedness,
            overall_teaching_satisfaction, recommendation_score,
            teacher_feedback, school_feedback, school_suggestions
        FROM survey
        WHERE (roll_number, school_name) IN %s
        """
        
        # Create tuple of tuples for IN clause
        keys_tuple = tuple((roll, school) for roll, school, _ in roll_school_pairs)
        cur.execute(fetch_full_sql, (keys_tuple,))
        full_rows = [dict(row) for row in cur.fetchall()]
        
        # STEP 3: Merge similarity scores with full rows
        similarity_map = {(r['roll_number'], r['school_name']): r['similarity'] 
                         for r in similarity_results}
        
        for row in full_rows:
            key = (row['roll_number'], row['school_name'])
            row['similarity_score'] = similarity_map.get(key, 0.0)
        
        # Sort by similarity score (descending)
        full_rows.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Extract feedback texts for summary
        feedback_texts = [row.get(feedback_column) for row in full_rows 
                         if row.get(feedback_column)]
        
        return {
            "success": True,
            "count": len(full_rows),
            "feedback": feedback_texts,
            "full_rows": full_rows,  # Complete database rows with all columns
            "details": full_rows,  # Keep for backward compatibility
            "warning": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        cur.close()
        conn.close()


def summarize_feedback(feedback_list: List[str], query: str) -> str:
    """Use LLM to summarize feedback themes"""
    if not feedback_list:
        return "No relevant feedback found."
    
    system_prompt = """You are a feedback analyst. Summarize the key themes from student feedback.

RULES:
- Identify 2-4 main themes/issues
- Be specific and actionable
- Include sentiment indicators
- Keep summary concise (3-5 sentences)
- Don't fabricate - only report what's in the feedback"""

    user_prompt = f"""Query context: {query}

Feedback to analyze:
{chr(10).join(f'- {fb}' for fb in feedback_list[:20])}

Provide a thematic summary."""

    return llm_call(system_prompt, user_prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: MIXED EXECUTION (QUANT + QUAL)
# ═══════════════════════════════════════════════════════════════════════════════

def run_mixed_analysis(query: str) -> Dict[str, Any]:
    """
    Run combined quantitative + qualitative analysis
    IMPROVED: Both quantitative and qualitative data are processed together by LLM
    First measures the issue with SQL, then finds relevant feedback with FULL rows
    """
    # Step 1: Run quantitative analysis first
    quant_result = run_quant_analysis(query)
    
    # Step 2: Determine which feedback to search based on query
    system_prompt = """Based on this query, determine:
1. Which feedback column to search: teacher_feedback, school_feedback, or school_suggestions
2. What semantic search query to use
3. Any filters to apply (class, subject_group, dissatisfied)

Return JSON: {"feedback_column": "...", "search_query": "...", "filters": {...}}"""

    search_config = llm_call(
        system_prompt,
        f"Query: {query}\n\nQuantitative results: {json.dumps(quant_result.get('results', [])[:5], cls=DecimalEncoder)}",
        json_mode=True
    )
    
    try:
        config = json.loads(search_config)
    except:
        config = {
            "feedback_column": "school_feedback",
            "search_query": query,
            "filters": {}
        }
    
    # Step 3: Run semantic search - now returns FULL database rows
    qual_result = run_semantic_search(
        config.get("search_query", query),
        config.get("feedback_column", "school_feedback"),
        config.get("filters"),
        limit=10
    )
    
    # Step 4: COMBINED LLM PROCESSING - Process both QUANT and QUAL data together
    combined_summary = ""
    if qual_result.get("success") and qual_result.get("full_rows"):
        combined_summary = process_mixed_data_with_llm(
            query=query,
            quant_data=quant_result,
            qual_data=qual_result,
            feedback_column=config.get("feedback_column", "school_feedback")
        )
    
    return {
        "quantitative": quant_result,
        "qualitative": {
            "feedback_count": qual_result.get("count", 0),
            "full_rows": qual_result.get("full_rows", []),  # Full database rows
            "combined_analysis": combined_summary,  # LLM analysis of both data types
            "sample_feedback": qual_result.get("feedback", [])[:5]
        }
    }


def process_mixed_data_with_llm(
    query: str,
    quant_data: Dict[str, Any],
    qual_data: Dict[str, Any],
    feedback_column: str
) -> str:
    """
    Process both quantitative metrics and qualitative feedback together using LLM
    This ensures the LLM considers both data types simultaneously for comprehensive insights
    """
    system_prompt = """You are an expert educational data analyst. Analyze both quantitative metrics 
and qualitative feedback TOGETHER to provide comprehensive insights.

YOUR TASK:
1. Connect the quantitative patterns with specific student feedback
2. Explain WHY the numbers look the way they do based on actual student voices
3. Identify specific, actionable issues mentioned by students
4. Provide evidence-based recommendations

RULES:
- Always reference both metrics AND specific feedback quotes
- Be specific about which student groups are affected
- Quantify issues when possible (e.g., "15% of students mentioned...")
- Keep response structured and concise (4-6 paragraphs max)
"""

    # Prepare quantitative summary
    quant_summary = {
        "sample_size": quant_data.get("sample_size", 0),
        "metrics": quant_data.get("results", [])[:10],
        "sql_query": quant_data.get("sql", "")
    }
    
    # Prepare qualitative data with FULL context
    full_rows = qual_data.get("full_rows", [])
    qual_summary = {
        "feedback_count": len(full_rows),
        "student_profiles": []
    }
    
    # Include full student profiles with similarity scores
    for row in full_rows[:10]:  # Top 10 most relevant
        profile = {
            "similarity_score": row.get("similarity_score", 0),
            "roll_number": row.get("roll_number"),
            "school_name": row.get("school_name"),
            "class": row.get("class"),
            "subject_group": row.get("subject_group"),
            "overall_teaching_satisfaction": row.get("overall_teaching_satisfaction"),
            "recommendation_score": row.get("recommendation_score"),
            "feedback": row.get(feedback_column, ""),
            # Include other relevant satisfaction metrics
            "teacher_support": row.get("teacher_support"),
            "lab_satisfaction": row.get("lab_satisfaction"),
            "transport_satisfaction": row.get("transport_satisfaction"),
            "career_guidance": row.get("career_guidance"),
            "competitive_exam_preparedness": row.get("competitive_exam_preparedness")
        }
        qual_summary["student_profiles"].append(profile)
    
    user_prompt = f"""QUERY: {query}

QUANTITATIVE DATA (Aggregated Metrics):
{json.dumps(quant_summary, indent=2, cls=DecimalEncoder)}

QUALITATIVE DATA (Individual Student Responses with Full Context):
{json.dumps(qual_summary, indent=2, cls=DecimalEncoder)}

INSTRUCTIONS:
Analyze both datasets TOGETHER. Explain the quantitative trends using the qualitative feedback.
Connect specific student concerns to the overall metrics. Provide actionable insights."""

    return llm_call(system_prompt, user_prompt)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN COPILOT FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def format_quant_response(result: Dict[str, Any], query: str) -> str:
    """Format quantitative results for display"""
    if not result.get("success"):
        return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    sample_size = result.get("sample_size", 0)
    results = result.get("results", [])
    warning = result.get("warning", "")
    
    # Use LLM to format response nicely
    system_prompt = """Format these survey analytics results clearly and concisely.

RULES:
- Always mention sample size first
- Show percentages with absolute counts: "45% (67 students)"
- Use bullet points for distributions
- Be factual, no speculation
- Keep it concise"""

    user_prompt = f"""Query: {query}
Sample Size: {sample_size}
Results: {json.dumps(results, indent=2, cls=DecimalEncoder)}
Warning: {warning}

Format this into a clear response."""

    return llm_call(system_prompt, user_prompt)


def format_qual_response(result: Dict[str, Any], query: str) -> str:
    """Format qualitative results for display"""
    if not result.get("success"):
        return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    count = result.get("count", 0)
    feedback = result.get("feedback", [])
    
    if count == 0:
        return "No relevant feedback found matching your query."
    
    summary = summarize_feedback(feedback, query)
    
    return f"""📝 **Feedback Analysis** (based on {count} relevant responses)

{summary}

**Sample Feedback:**
{chr(10).join(f'• "{fb}"' for fb in feedback[:3])}"""


def format_mixed_response(result: Dict[str, Any], query: str) -> str:
    """
    Format mixed analysis results
    IMPROVED: Uses combined LLM analysis that processes both data types together
    """
    quant = result.get("quantitative", {})
    qual = result.get("qualitative", {})
    
    response_parts = []
    
    # Check if we have combined analysis (new approach)
    if qual.get("combined_analysis"):
        # NEW: Use the combined LLM analysis that processed both data types together
        response_parts.append("🔍 **INTEGRATED ANALYSIS** (Quantitative + Qualitative)")
        response_parts.append(f"Sample Size: {quant.get('sample_size', 0)} | Feedback Responses: {qual.get('feedback_count', 0)}")
        response_parts.append("\n" + qual["combined_analysis"])
        
        # Add data summary section
        response_parts.append("\n" + "─" * 40)
        response_parts.append("📊 **Raw Quantitative Data:**")
        for row in quant.get("results", [])[:5]:
            items = [f"{k}: {v}" for k, v in row.items()]
            response_parts.append("  • " + ", ".join(items))
        
        # Show sample of actual student feedback with context
        if qual.get("full_rows"):
            response_parts.append("\n💬 **Student Profiles (with similarity scores):**")
            for idx, row in enumerate(qual["full_rows"][:3], 1):
                response_parts.append(f"\n  [{idx}] Roll: {row.get('roll_number')} | School: {row.get('school_name')} | Similarity: {row.get('similarity_score', 0):.3f}")
                response_parts.append(f"      Class: {row.get('class')} | Subject: {row.get('subject_group')}")
                response_parts.append(f"      Satisfaction: {row.get('overall_teaching_satisfaction')}")
                feedback = row.get(qual.get("feedback_column", "school_feedback"), "")
                if feedback:
                    response_parts.append(f'      Feedback: "{feedback[:150]}..."' if len(feedback) > 150 else f'      Feedback: "{feedback}"')
    
    else:
        # FALLBACK: Old format if combined analysis not available
        if quant.get("success"):
            sample_size = quant.get("sample_size", 0)
            results = quant.get("results", [])
            response_parts.append(f"📊 **Metrics** (n={sample_size})")
            
            for row in results[:10]:
                items = [f"{k}: {v}" for k, v in row.items()]
                response_parts.append("  • " + ", ".join(items))
        
        if qual.get("sample_feedback"):
            response_parts.append(f"\n💬 **Feedback Insights** ({qual.get('feedback_count', 0)} relevant responses)")
            response_parts.append("\n**Examples:**")
            for fb in qual["sample_feedback"][:3]:
                response_parts.append(f'• "{fb}"')
    
    return "\n".join(response_parts)


def ask_survey(query: str) -> str:
    """
    Main entry point for the survey copilot
    Routes query, executes analysis, and returns formatted response
    """
    print(f"\n🔍 Query: {query}")
    
    # Step 1: Classify intent
    intent = classify_intent(query)
    print(f"📌 Intent: {intent}")
    
    # Step 2: Execute based on intent
    if intent == "QUANT":
        result = run_quant_analysis(query)
        response = format_quant_response(result, query)
        
    elif intent == "QUAL":
        # Determine feedback column
        if "teacher" in query.lower():
            feedback_col = "teacher_feedback"
        elif "suggestion" in query.lower():
            feedback_col = "school_suggestions"
        else:
            feedback_col = "school_feedback"
        
        result = run_semantic_search(query, feedback_col)
        response = format_qual_response(result, query)
        
    else:  # MIXED
        result = run_mixed_analysis(query)
        response = format_mixed_response(result, query)
    
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Interactive CLI for survey copilot"""
    print("=" * 60)
    print("🎓 SMART SURVEY ANALYTICS COPILOT")
    print("=" * 60)
    print("Powered by PostgreSQL + pgvector + GPT-4")
    print("\nExample queries:")
    print("  • What is the average satisfaction with teaching?")
    print("  • Show transport satisfaction distribution by class")
    print("  • What do students complain about regarding labs?")
    print("  • Why is competitive exam preparedness rated low?")
    print("\nType 'quit' to exit\n")
    
    while True:
        try:
            query = input("📝 Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                continue
            
            response = ask_survey(query)
            print("\n" + "─" * 40)
            print(response)
            print("─" * 40 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
