"""
load_recent_data.py
Load recent survey data from Google Sheets into PostgreSQL
- Checks for duplicates based on (student_name, roll_number)
- Handles missing open-ended responses (skips embedding generation)
- Logs what data was skipped and what was added with embeddings
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

load_dotenv()

# Database configuration - use Unix socket with peer authentication
DB_CONFIG = {
    "database": "smart_survey",
    "user": "postgres",
    "host": "/var/run/postgresql",
    "port": "5433"
}

# OpenAI for embeddings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Google Sheets URL
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1vUaqyt6ibyrsEm0S-LBAQSBUJMSPBX6TLESOSpBr-9Y/edit?resourcekey=&gid=1394571568#gid=1394571568"

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
        'everything good', 'all good', 'no issues', 'no suggestions',
        'need better labs', 'more sports facilities', 'improve library',
        'need more examples', 'better revision', 'improve punctuality',
        'improve teaching', 'more activities', 'reduce pressure',
        'good teaching overall', 'need more practice problems',
        'classes are too fast', 'want more doubt sessions',
        'teachers are helpful', 'need more explanation',
        'good infrastructure', 'better canteen food needed',
        'improve transport', 'more activities needed',
        'clean washrooms needed', 'good overall',
        'better facilities', 'more sports events',
        'improve labs', 'better career guidance',
        'more field trips', 'no suggestions'
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

def load_google_sheets_data():
    """Load data from Google Sheets and insert into database"""
    print("🚀 Loading recent data from Google Sheets...")
    print(f"📎 Google Sheets URL: {SHEETS_URL}")
    
    # Convert Google Sheets URL to CSV export URL
    sheet_id = "1vUaqyt6ibyrsEm0S-LBAQSBUJMSPBX6TLESOSpBr-9Y"
    gid = "1394571568"
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    print(f"📥 Downloading data from Google Sheets...")
    try:
        df = pd.read_csv(csv_url)
        print(f"✅ Successfully loaded {len(df)} rows from Google Sheets")
    except Exception as e:
        print(f"❌ Error loading Google Sheets: {e}")
        return
    
    # Map CSV columns to database columns (same schema as existing data)
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
    
    # Statistics tracking
    total_rows = len(df)
    skipped_duplicates = []
    added_records = []
    records_without_embeddings = []
    
    print(f"\n📊 Processing {total_rows} rows from Google Sheets...")
    print("=" * 80)
    
    for idx, row in df.iterrows():
        # Extract basic identity fields first
        student_name = str(row.get('Your name', '')).strip() if pd.notna(row.get('Your name')) else None
        roll_number = str(row.get('Roll Number', '')).strip() if pd.notna(row.get('Roll Number')) else None
        
        # Check for duplicate
        if check_duplicate_exists(conn, student_name, roll_number):
            skipped_duplicates.append({
                'name': student_name,
                'roll_number': roll_number,
                'reason': 'Duplicate (name + roll_number already exists in DB)'
            })
            print(f"⏭️  Row {idx + 1}: SKIPPED - Duplicate: {student_name} ({roll_number})")
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
        
        # Check open-ended responses and generate embeddings
        teacher_feedback_text = values.get('teacher_feedback')
        school_feedback_text = values.get('school_feedback')
        school_suggestions_text = values.get('school_suggestions')
        
        # Generate embeddings (will be None if text is invalid/missing)
        teacher_emb = generate_embedding(teacher_feedback_text)
        school_emb = generate_embedding(school_feedback_text)
        suggestions_emb = generate_embedding(school_suggestions_text)
        
        # Track embedding generation
        embedding_info = {
            'teacher_feedback': 'Yes' if teacher_emb else 'No (missing/invalid)',
            'school_feedback': 'Yes' if school_emb else 'No (missing/invalid)',
            'school_suggestions': 'Yes' if suggestions_emb else 'No (missing/invalid)'
        }
        
        has_any_embedding = any([teacher_emb, school_emb, suggestions_emb])
        
        # Insert row into database
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
            
            # Track added record
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
            
            print(f"✅ Row {idx + 1}: ADDED - {student_name} ({roll_number})")
            print(f"    📝 Embeddings: Teacher={embedding_info['teacher_feedback']}, "
                  f"School={embedding_info['school_feedback']}, "
                  f"Suggestions={embedding_info['school_suggestions']}")
            
        except Exception as e:
            print(f"❌ Row {idx + 1}: ERROR - Failed to insert: {e}")
            conn.rollback()
        finally:
            cur.close()
    
    conn.close()
    
    # Print summary report
    print("\n" + "=" * 80)
    print("📊 SUMMARY REPORT")
    print("=" * 80)
    print(f"Total rows processed: {total_rows}")
    print(f"✅ Records added to database: {len(added_records)}")
    print(f"⏭️  Records skipped (duplicates): {len(skipped_duplicates)}")
    print(f"⚠️  Records added without embeddings: {len(records_without_embeddings)}")
    
    # Detail: Skipped duplicates
    if skipped_duplicates:
        print(f"\n{'─' * 80}")
        print("⏭️  SKIPPED RECORDS (Duplicates):")
        print(f"{'─' * 80}")
        for i, dup in enumerate(skipped_duplicates, 1):
            print(f"{i}. {dup['name']} (Roll: {dup['roll_number']}) - {dup['reason']}")
    
    # Detail: Added records
    if added_records:
        print(f"\n{'─' * 80}")
        print("✅ ADDED RECORDS:")
        print(f"{'─' * 80}")
        for i, rec in enumerate(added_records, 1):
            print(f"{i}. {rec['name']} (Roll: {rec['roll_number']}) - {rec['school']}")
            print(f"   Embeddings Generated:")
            print(f"     • Teacher Feedback: {rec['embeddings']['teacher_feedback']}")
            print(f"     • School Feedback: {rec['embeddings']['school_feedback']}")
            print(f"     • School Suggestions: {rec['embeddings']['school_suggestions']}")
    
    # Detail: Records without embeddings
    if records_without_embeddings:
        print(f"\n{'─' * 80}")
        print("⚠️  RECORDS ADDED WITHOUT ANY EMBEDDINGS (missing/invalid open-ended responses):")
        print(f"{'─' * 80}")
        for i, rec in enumerate(records_without_embeddings, 1):
            print(f"{i}. {rec['name']} (Roll: {rec['roll_number']})")
    
    print("\n" + "=" * 80)
    print("✅ Load complete!")
    print("=" * 80)

def verify_database_status():
    """Show current database status"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Total records
    cur.execute("SELECT COUNT(*) FROM survey;")
    total = cur.fetchone()[0]
    
    # Records with embeddings
    cur.execute("SELECT COUNT(*) FROM survey WHERE teacher_feedback_embedding IS NOT NULL;")
    teacher_emb = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM survey WHERE school_feedback_embedding IS NOT NULL;")
    school_emb = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM survey WHERE school_suggestions_embedding IS NOT NULL;")
    suggestions_emb = cur.fetchone()[0]
    
    print(f"\n📊 Current Database Status:")
    print(f"   Total records: {total}")
    print(f"   Teacher feedback embeddings: {teacher_emb}")
    print(f"   School feedback embeddings: {school_emb}")
    print(f"   School suggestions embeddings: {suggestions_emb}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("🚀 Smart Survey - Load Recent Data from Google Sheets")
    print("=" * 80)
    
    # Show current status
    verify_database_status()
    
    print("\n" + "=" * 80)
    
    # Load new data
    load_google_sheets_data()
    
    # Show updated status
    verify_database_status()
