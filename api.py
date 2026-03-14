"""
api.py
FastAPI application for Smart Survey Analytics

Endpoints:
1. GET /status - Database status with records by school, class, and subject group
2. POST /load-recent - Load recent data from Google Sheets with change summary
3. DELETE /delete/by-roll-school - Delete by Roll Number + School Name
4. DELETE /delete/by-school - Delete by School Name
5. DELETE /delete/by-class - Delete by Class (+ optional Subject Group)
6. POST /search - Search with intent detection, similarity scores, and chart generation
7. GET /chart/{filename} - Download generated chart files
8. GET /charts - List all available charts
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from urllib.parse import quote as url_quote

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd

# Import existing utilities
from survey_copilot import (
    classify_intent, 
    run_quant_analysis, 
    run_semantic_search,
    run_mixed_analysis,
    generate_query_embedding,
    generate_chart,
    get_connection as copilot_get_connection
)

# Output directory for charts
CHART_OUTPUT_DIR = Path("smart_outputs")
CHART_OUTPUT_DIR.mkdir(exist_ok=True)

load_dotenv()

# Database configuration
DB_CONFIG = {
    "database": os.getenv("DB_NAME", "smart_survey"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# OpenAI for embeddings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Google Sheets URL
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1vUaqyt6ibyrsEm0S-LBAQSBUJMSPBX6TLESOSpBr-9Y/edit?resourcekey=&gid=1394571568#gid=1394571568"

# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI App Setup
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Smart Survey Analytics API",
    description="API for managing and analyzing school survey data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# Custom JSON Encoder for Decimal
# ═══════════════════════════════════════════════════════════════════════════════

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════

class DeleteByRollSchoolRequest(BaseModel):
    roll_number: str = Field(..., description="Student roll number")
    school_name: str = Field(..., description="School name")

class DeleteBySchoolRequest(BaseModel):
    school_name: str = Field(..., description="School name")

class DeleteByClassRequest(BaseModel):
    class_name: str = Field(..., description="Class name (e.g., '5th', '10th')")
    subject_group: Optional[str] = Field(None, description="Optional subject group filter")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    feedback_column: Optional[str] = Field("school_feedback", description="Which feedback column to search: teacher_feedback, school_feedback, or school_suggestions")
    limit: Optional[int] = Field(10, description="Maximum number of results")

# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def is_valid_feedback(text):
    """Check if text is valid for embedding generation"""
    if not text or pd.isna(text):
        return False
    
    text_original = str(text).strip()
    text_lower = text_original.lower()
    
    # Long feedback (>50 chars) is always valid
    if len(text_original) > 50:
        return True
    
    # Short text needs more validation
    if len(text_original) < 15:
        return False
    
    alpha_count = sum(1 for c in text_original if c.isalpha())
    if alpha_count < len(text_original) * 0.5:
        return False
    
    # List of short generic responses to skip
    invalid_responses = [
        'no concerns', 'none', 'na', 'n/a', 'nothing', 'ok', 'okay', 'good',
        'fine', 'nice', 'no', 'yes', 'no comment', 'no comments', 'nil',
        'everything good', 'all good', 'no issues', 'no suggestions'
    ]
    
    return text_lower not in invalid_responses

def generate_embedding(text):
    """Generate embedding using OpenAI text-embedding-3-small"""
    if not is_valid_feedback(text):
        return None
    
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=str(text)
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"    ⚠️  Embedding error: {e}")
        return None

def check_duplicate_exists(conn, student_name, roll_number):
    """Check if a record with same student_name and roll_number exists"""
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM survey 
        WHERE student_name = %s AND roll_number = %s
        LIMIT 1
    """, (student_name, roll_number))
    result = cur.fetchone()
    cur.close()
    return result is not None

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 1: STATUS - Get database status with aggregations
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/status", tags=["Status"])
async def get_status():
    """
    Get database status showing:
    - Total records
    - Records by school
    - Records by class with subject group breakdown
    """
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total records
        cur.execute("SELECT COUNT(*) as total FROM survey")
        total_records = cur.fetchone()['total']
        
        # Records by school
        cur.execute("""
            SELECT school_name, COUNT(*) as count
            FROM survey
            GROUP BY school_name
            ORDER BY school_name
        """)
        by_school = [dict(row) for row in cur.fetchall()]
        
        # Records by class
        cur.execute("""
            SELECT class, COUNT(*) as count
            FROM survey
            GROUP BY class
            ORDER BY class
        """)
        by_class = [dict(row) for row in cur.fetchall()]
        
        # Records by class and subject group (nested structure)
        cur.execute("""
            SELECT 
                class,
                subject_group,
                COUNT(*) as count
            FROM survey
            GROUP BY class, subject_group
            ORDER BY class, subject_group
        """)
        class_subject_results = [dict(row) for row in cur.fetchall()]
        
        # Organize by class with subject groups
        by_class_with_subjects = {}
        for row in class_subject_results:
            class_name = row['class']
            subject_group = row['subject_group']
            count = row['count']
            
            if class_name not in by_class_with_subjects:
                by_class_with_subjects[class_name] = {
                    'total': 0,
                    'subject_groups': {}
                }
            
            by_class_with_subjects[class_name]['subject_groups'][subject_group] = count
            by_class_with_subjects[class_name]['total'] += count
        
        # Records with embeddings
        cur.execute("SELECT COUNT(*) as count FROM survey WHERE teacher_feedback_embedding IS NOT NULL")
        teacher_embeddings = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM survey WHERE school_feedback_embedding IS NOT NULL")
        school_embeddings = cur.fetchone()['count']
        
        cur.execute("SELECT COUNT(*) as count FROM survey WHERE school_suggestions_embedding IS NOT NULL")
        suggestions_embeddings = cur.fetchone()['count']
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_records": total_records,
            "embeddings": {
                "teacher_feedback": teacher_embeddings,
                "school_feedback": school_embeddings,
                "school_suggestions": suggestions_embeddings
            },
            "by_school": by_school,
            "by_class": by_class,
            "by_class_with_subject_groups": by_class_with_subjects
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 2: LOAD RECENT DATA - Load from Google Sheets with summary
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/load-recent", tags=["Data Management"])
async def load_recent_data():
    """
    Load recent data from Google Sheets and return summary:
    - What changed in DB
    - What rows were added
    - Final status
    """
    try:
        # Convert Google Sheets URL to CSV export URL
        sheet_id = "1vUaqyt6ibyrsEm0S-LBAQSBUJMSPBX6TLESOSpBr-9Y"
        gid = "1394571568"
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        
        # Load data from Google Sheets
        df = pd.read_csv(csv_url)
        total_rows = len(df)
        
        # Column mapping
        column_mapping = {
            'Timestamp': 'timestamp',
            'Your name': 'student_name',
            'Roll Number': 'roll_number',
            'Your school name': 'school_name',
            'Your class': 'class',
            'What was your last year overall percentage or CGPA?': 'last_year_percentage',
            'How much time do you spend every day on your self study and homework?': 'study_time',
            'Which is your least favourite or toughest subject?': 'toughest_subject',
            'Subject group': 'subject_group',
            'Choose Subject Where The Subject Teacher Rating is [Excellent]': 'teacher_rating_excellent',
            'Choose Subject Where The Subject Teacher Rating is [Very Good]': 'teacher_rating_very_good',
            'Choose Subject Where The Subject Teacher Rating is [Good]': 'teacher_rating_good',
            'Choose Subject Where The Subject Teacher Rating is [Average]': 'teacher_rating_average',
            'Choose Subject Where The Subject Teacher Rating is [Poor]': 'teacher_rating_poor',
            'Do teachers provide enough support for your academic learning and solving queries?': 'teacher_support',
            'How do you meet your academic learning goal?': 'learning_goal_method',
            'How well do teachers give real-world applications or examples in class?': 'real_world_examples',
            'Does your faculty encourage you to ask questions and create an interactive classroom?': 'interactive_classroom',
            'Please add your suggestions or concern related to any teacher.': 'teacher_feedback',
            'Does your school have sufficient availability of computer or science labs and libraries that enhance your learning experience?': 'lab_satisfaction',
            'Are there sufficient resources for extracurricular activities like music, sports, yoga, dancing, art & crafts?': 'extracurricular_resources',
            'Does your school conduct events that encourage creativity, innovation, and leadership?': 'school_events',
            'How satisfied are you with the transportation facilities provided by school?': 'transport_satisfaction',
            'Does your school provide career guidance and academic counselling?': 'career_guidance',
            'Please share any suggestions or concerns about your school facilities.': 'school_feedback',
            'How well does your school resolve issues of bullying and harassment?': 'bullying_resolution',
            'School behaviour towards challenges like late fees or fee concessions?': 'fee_behaviour',
            'Do you feel that there is a fair and transparent exam results and paper checking?': 'exam_fairness',
            'Does your school handle academic stress and wellness issues?': 'wellness_support',
            'Do you think your school adequately prepared you for competitive exams?': 'competitive_exam_preparedness',
            'How satisfied are you with the overall quality of teaching at the school?': 'overall_teaching_satisfaction',
            'How would you recommend this school to your friends?': 'recommendation_score',
            'Please share any suggestions or concerns about your school.': 'school_suggestions'
        }
        
        conn = get_connection()
        
        # Get initial status
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM survey")
        initial_count = cur.fetchone()[0]
        cur.close()
        
        # Process rows
        skipped_duplicates = []
        added_records = []
        records_without_embeddings = []
        
        for idx, row in df.iterrows():
            # Extract basic identity fields
            student_name = str(row.get('Your name', '')).strip() if pd.notna(row.get('Your name')) else None
            roll_number = str(row.get('Roll Number', '')).strip() if pd.notna(row.get('Roll Number')) else None
            
            # Check for duplicate
            if check_duplicate_exists(conn, student_name, roll_number):
                skipped_duplicates.append({
                    'name': student_name,
                    'roll_number': roll_number,
                    'reason': 'Duplicate (name + roll_number already exists)'
                })
                continue
            
            # Extract all values
            values = {}
            for csv_col, db_col in column_mapping.items():
                if csv_col in df.columns:
                    val = row[csv_col]
                    if pd.isna(val):
                        values[db_col] = None
                    elif db_col == 'timestamp':
                        try:
                            values[db_col] = pd.to_datetime(val, format='%d/%m/%Y %H:%M:%S')
                        except:
                            try:
                                values[db_col] = pd.to_datetime(val)
                            except:
                                values[db_col] = None
                    elif db_col == 'recommendation_score':
                        try:
                            values[db_col] = int(val)
                        except:
                            values[db_col] = None
                    elif db_col == 'last_year_percentage':
                        try:
                            values[db_col] = float(val)
                        except:
                            values[db_col] = None
                    else:
                        values[db_col] = str(val)
                else:
                    values[db_col] = None
            
            # Generate embeddings
            teacher_emb = generate_embedding(values.get('teacher_feedback'))
            school_emb = generate_embedding(values.get('school_feedback'))
            suggestions_emb = generate_embedding(values.get('school_suggestions'))
            
            embedding_info = {
                'teacher_feedback': 'Yes' if teacher_emb else 'No',
                'school_feedback': 'Yes' if school_emb else 'No',
                'school_suggestions': 'Yes' if suggestions_emb else 'No'
            }
            
            has_any_embedding = any([teacher_emb, school_emb, suggestions_emb])
            
            # Insert row
            cur = conn.cursor()
            insert_sql = """
            INSERT INTO survey (
                timestamp, student_name, roll_number, school_name, class, last_year_percentage,
                study_time, toughest_subject, subject_group,
                teacher_rating_excellent, teacher_rating_very_good, teacher_rating_good,
                teacher_rating_average, teacher_rating_poor,
                teacher_support, learning_goal_method, real_world_examples, interactive_classroom,
                teacher_feedback, lab_satisfaction, extracurricular_resources, school_events,
                transport_satisfaction, career_guidance, school_feedback,
                bullying_resolution, fee_behaviour, exam_fairness, wellness_support,
                competitive_exam_preparedness, overall_teaching_satisfaction, recommendation_score,
                school_suggestions,
                teacher_feedback_embedding, school_feedback_embedding, school_suggestions_embedding
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            try:
                cur.execute(insert_sql, (
                    values.get('timestamp'), values.get('student_name'), values.get('roll_number'),
                    values.get('school_name'), values.get('class'), values.get('last_year_percentage'),
                    values.get('study_time'), values.get('toughest_subject'), values.get('subject_group'),
                    values.get('teacher_rating_excellent'), values.get('teacher_rating_very_good'),
                    values.get('teacher_rating_good'), values.get('teacher_rating_average'),
                    values.get('teacher_rating_poor'), values.get('teacher_support'),
                    values.get('learning_goal_method'), values.get('real_world_examples'),
                    values.get('interactive_classroom'), values.get('teacher_feedback'),
                    values.get('lab_satisfaction'), values.get('extracurricular_resources'),
                    values.get('school_events'), values.get('transport_satisfaction'),
                    values.get('career_guidance'), values.get('school_feedback'),
                    values.get('bullying_resolution'), values.get('fee_behaviour'),
                    values.get('exam_fairness'), values.get('wellness_support'),
                    values.get('competitive_exam_preparedness'), values.get('overall_teaching_satisfaction'),
                    values.get('recommendation_score'), values.get('school_suggestions'),
                    teacher_emb, school_emb, suggestions_emb
                ))
                conn.commit()
                
                added_records.append({
                    'name': student_name,
                    'roll_number': roll_number,
                    'school': values.get('school_name'),
                    'embeddings': embedding_info
                })
                
                if not has_any_embedding:
                    records_without_embeddings.append({
                        'name': student_name,
                        'roll_number': roll_number
                    })
            except Exception as e:
                conn.rollback()
                print(f"Error inserting row: {e}")
            finally:
                cur.close()
        
        # Get final status
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM survey")
        final_count = cur.fetchone()[0]
        cur.close()
        
        conn.close()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "sheets_url": SHEETS_URL,
            "summary": {
                "total_rows_in_sheet": total_rows,
                "records_added": len(added_records),
                "records_skipped": len(skipped_duplicates),
                "records_without_embeddings": len(records_without_embeddings)
            },
            "database_change": {
                "before": initial_count,
                "after": final_count,
                "change": final_count - initial_count
            },
            "added_records": added_records,
            "skipped_records": skipped_duplicates,
            "records_without_embeddings": records_without_embeddings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 3: DELETE by Roll Number + School Name
# ═══════════════════════════════════════════════════════════════════════════════

@app.delete("/delete/by-roll-school", tags=["Delete Operations"])
async def delete_by_roll_school(request: DeleteByRollSchoolRequest):
    """Delete records by Roll Number and School Name"""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Preview records
        preview_sql = """
            SELECT id, student_name, roll_number, school_name, class, subject_group
            FROM survey
            WHERE roll_number = %s AND school_name = %s
        """
        cur.execute(preview_sql, (request.roll_number, request.school_name))
        records = [dict(row) for row in cur.fetchall()]
        
        if not records:
            cur.close()
            conn.close()
            return {
                "status": "warning",
                "message": "No records found matching criteria",
                "deleted_count": 0
            }
        
        # Delete records
        delete_sql = "DELETE FROM survey WHERE roll_number = %s AND school_name = %s"
        cur.execute(delete_sql, (request.roll_number, request.school_name))
        deleted_count = cur.rowcount
        conn.commit()
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Successfully deleted {deleted_count} record(s)",
            "deleted_count": deleted_count,
            "deleted_records": records
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 4: DELETE by School Name
# ═══════════════════════════════════════════════════════════════════════════════

@app.delete("/delete/by-school", tags=["Delete Operations"])
async def delete_by_school(request: DeleteBySchoolRequest):
    """Delete all records from a specific school"""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Preview records
        preview_sql = """
            SELECT id, student_name, roll_number, school_name, class, subject_group
            FROM survey
            WHERE school_name = %s
        """
        cur.execute(preview_sql, (request.school_name,))
        records = [dict(row) for row in cur.fetchall()]
        
        if not records:
            cur.close()
            conn.close()
            return {
                "status": "warning",
                "message": f"No records found for school: {request.school_name}",
                "deleted_count": 0
            }
        
        # Delete records
        delete_sql = "DELETE FROM survey WHERE school_name = %s"
        cur.execute(delete_sql, (request.school_name,))
        deleted_count = cur.rowcount
        conn.commit()
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Successfully deleted {deleted_count} record(s) from {request.school_name}",
            "deleted_count": deleted_count,
            "deleted_records": records
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 5: DELETE by Class (+ optional Subject Group)
# ═══════════════════════════════════════════════════════════════════════════════

@app.delete("/delete/by-class", tags=["Delete Operations"])
async def delete_by_class(request: DeleteByClassRequest):
    """Delete records by Class and optionally Subject Group"""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query based on whether subject_group is provided
        if request.subject_group:
            where_clause = "class = %s AND subject_group = %s"
            params = (request.class_name, request.subject_group)
        else:
            where_clause = "class = %s"
            params = (request.class_name,)
        
        # Preview records
        preview_sql = f"""
            SELECT id, student_name, roll_number, school_name, class, subject_group
            FROM survey
            WHERE {where_clause}
        """
        cur.execute(preview_sql, params)
        records = [dict(row) for row in cur.fetchall()]
        
        if not records:
            cur.close()
            conn.close()
            return {
                "status": "warning",
                "message": "No records found matching criteria",
                "deleted_count": 0
            }
        
        # Delete records
        delete_sql = f"DELETE FROM survey WHERE {where_clause}"
        cur.execute(delete_sql, params)
        deleted_count = cur.rowcount
        conn.commit()
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Successfully deleted {deleted_count} record(s)",
            "deleted_count": deleted_count,
            "deleted_records": records,
            "filters": {
                "class": request.class_name,
                "subject_group": request.subject_group
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 6: SEARCH with intent detection and similarity scores
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/search", tags=["Search & Analytics"])
async def search_query(request: SearchRequest):
    """
    Search with intent detection and return results with similarity scores
    
    Returns:
    - intent: QUANT, QUAL, or MIXED
    - final_response: Human-readable answer
    - Retrieved rows with similarity scores (for vector search)
    - Numbers in JSON format for graph generation
    - chart_url: URL to download the generated chart (for QUANT and MIXED intents)
    """
    try:
        query = request.query
        
        # Step 1: Classify intent
        intent = classify_intent(query)
        
        # Step 2: Execute based on intent
        if intent == "QUANT":
            # Quantitative analysis
            result = run_quant_analysis(query)
            
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error", "Query execution failed"))
            
            # Generate chart for quantitative results
            chart_path = None
            chart_url = None
            results_data = result.get("results", [])
            if results_data:
                chart_path = generate_chart(results_data, query)
                if chart_path:
                    # Extract just the filename (without /chart/ prefix)
                    chart_filename = Path(chart_path).name
                    chart_url = chart_filename
            
            return {
                "status": "success",
                "intent": intent,
                "final_response": format_quant_response_api(result, query),
                "chart_url": chart_url,
                "chart_info": {
                    "generated": chart_path is not None,
                    "message": "Chart generated successfully. Use chart_url to download." if chart_url else "No chart generated (insufficient data)"
                },
                "retrieved_rows": {
                    "type": "aggregated",
                    "data": results_data,
                    "sample_size": result.get("sample_size", 0),
                    "similarity_scores": "N/A (quantitative query)"
                },
                "numbers_for_graph": {
                    "mixed": "N/A",
                    "quant": results_data
                },
                "sql_query": result.get("sql", "")
            }
            
        elif intent == "QUAL":
            # Qualitative analysis - semantic search
            result = run_semantic_search(
                query, 
                request.feedback_column,
                limit=request.limit
            )
            
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error", "Search failed"))
            
            # Extract rows with similarity scores
            full_rows = result.get("full_rows", [])
            
            return {
                "status": "success",
                "intent": intent,
                "final_response": format_qual_response_api(result, query),
                "chart_url": None,
                "chart_info": {
                    "generated": False,
                    "message": "Charts are not generated for qualitative (QUAL) queries"
                },
                "retrieved_rows": {
                    "type": "vector_search",
                    "count": result.get("count", 0),
                    "data": full_rows,
                    "similarity_scores": [
                        {
                            "roll_number": row.get("roll_number"),
                            "school_name": row.get("school_name"),
                            "similarity": row.get("similarity_score", 0)
                        } 
                        for row in full_rows
                    ]
                },
                "numbers_for_graph": {
                    "mixed": "N/A",
                    "quant": "N/A (qualitative query)"
                }
            }
            
        else:  # MIXED
            # Combined analysis
            result = run_mixed_analysis(query)
            
            quant = result.get("quantitative", {})
            qual = result.get("qualitative", {})
            
            # Get full rows with similarity scores
            full_rows = qual.get("full_rows", [])
            
            # Generate chart for mixed results (using quantitative data)
            chart_path = None
            chart_url = None
            quant_results = quant.get("results", [])
            if quant_results:
                chart_path = generate_chart(quant_results, query)
                if chart_path:
                    chart_filename = Path(chart_path).name
                    chart_url = chart_filename
            
            return {
                "status": "success",
                "intent": intent,
                "final_response": format_mixed_response_api(result, query),
                "chart_url": chart_url,
                "chart_info": {
                    "generated": chart_path is not None,
                    "message": "Chart generated successfully. Use chart_url to download." if chart_url else "No chart generated (insufficient data)"
                },
                "retrieved_rows": {
                    "type": "mixed",
                    "quantitative": {
                        "sample_size": quant.get("sample_size", 0),
                        "data": quant_results
                    },
                    "qualitative": {
                        "count": qual.get("feedback_count", 0),
                        "data": full_rows,
                        "similarity_scores": [
                            {
                                "roll_number": row.get("roll_number"),
                                "school_name": row.get("school_name"),
                                "similarity": row.get("similarity_score", 0)
                            } 
                            for row in full_rows
                        ]
                    }
                },
                "numbers_for_graph": {
                    "mixed": {
                        "quantitative": quant_results,
                        "qualitative_count": qual.get("feedback_count", 0)
                    },
                    "quant": quant_results
                },
                "sql_query": quant.get("sql", "")
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT 7: CHART DOWNLOAD - Serve generated chart files
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/chart/{filename}", tags=["Charts"])
async def download_chart(filename: str):
    """
    Download a generated chart file
    
    Args:
        filename: The chart filename (e.g., chart_satisfaction_20260314_141500.png)
    
    Returns:
        The chart image file as a downloadable PNG
    """
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Construct full path
    chart_path = CHART_OUTPUT_DIR / filename
    
    # Check if file exists
    if not chart_path.exists():
        raise HTTPException(status_code=404, detail=f"Chart not found: {filename}")
    
    # Return file as downloadable response
    return FileResponse(
        path=str(chart_path),
        media_type="image/png",
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.get("/charts", tags=["Charts"])
async def list_charts():
    """
    List all available chart files
    
    Returns:
        List of chart filenames with their creation timestamps
    """
    charts = []
    for chart_file in CHART_OUTPUT_DIR.glob("*.png"):
        stat = chart_file.stat()
        charts.append({
            "filename": chart_file.name,
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
        })
    
    # Sort by creation time (newest first)
    charts.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "status": "success",
        "total_charts": len(charts),
        "charts": charts
    }

# ═══════════════════════════════════════════════════════════════════════════════
# Response Formatting Functions
# ═══════════════════════════════════════════════════════════════════════════════

def format_quant_response_api(result: Dict[str, Any], query: str) -> str:
    """Format quantitative results for API response"""
    sample_size = result.get("sample_size", 0)
    results = result.get("results", [])
    warning = result.get("warning", "")
    
    response_parts = [
        f"**Query:** {query}",
        f"**Sample Size:** {sample_size}",
        ""
    ]
    
    if warning:
        response_parts.append(f"⚠️ {warning}\n")
    
    response_parts.append("**Results:**")
    for i, row in enumerate(results[:10], 1):
        items = [f"{k}: {v}" for k, v in row.items()]
        response_parts.append(f"{i}. {', '.join(items)}")
    
    return "\n".join(response_parts)

def format_qual_response_api(result: Dict[str, Any], query: str) -> str:
    """Format qualitative results for API response"""
    count = result.get("count", 0)
    full_rows = result.get("full_rows", [])
    
    if count == 0:
        return "No relevant feedback found matching your query."
    
    response_parts = [
        f"**Query:** {query}",
        f"**Found:** {count} relevant responses",
        "",
        "**Top Matching Feedback:**"
    ]
    
    for i, row in enumerate(full_rows[:5], 1):
        response_parts.append(f"\n{i}. **Student:** {row.get('student_name')} (Roll: {row.get('roll_number')})")
        response_parts.append(f"   **School:** {row.get('school_name')} | **Class:** {row.get('class')}")
        response_parts.append(f"   **Similarity Score:** {row.get('similarity_score', 0):.3f}")
        
        # Get feedback text
        for feedback_col in ['teacher_feedback', 'school_feedback', 'school_suggestions']:
            feedback = row.get(feedback_col)
            if feedback:
                response_parts.append(f'   **Feedback:** "{feedback}"')
                break
    
    return "\n".join(response_parts)

def format_mixed_response_api(result: Dict[str, Any], query: str) -> str:
    """Format mixed analysis results for API response"""
    quant = result.get("quantitative", {})
    qual = result.get("qualitative", {})
    
    response_parts = [
        f"**Query:** {query}",
        "",
        "**COMBINED ANALYSIS (Quantitative + Qualitative)**",
        f"Sample Size: {quant.get('sample_size', 0)} | Feedback Responses: {qual.get('feedback_count', 0)}",
        ""
    ]
    
    # Add combined analysis if available
    if qual.get("combined_analysis"):
        response_parts.append(qual["combined_analysis"])
    
    return "\n".join(response_parts)

# ═══════════════════════════════════════════════════════════════════════════════
# Root and Health Check
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
async def root():
    """API root endpoint"""
    return {
        "message": "Smart Survey Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "status": "/status",
            "load_recent": "/load-recent",
            "delete_by_roll_school": "/delete/by-roll-school",
            "delete_by_school": "/delete/by-school",
            "delete_by_class": "/delete/by-class",
            "search": "/search (generates charts for QUANT/MIXED intents)",
            "chart_download": "/chart/{filename}",
            "chart_list": "/charts"
        },
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
