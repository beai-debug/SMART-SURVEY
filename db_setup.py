"""
db_setup.py
Database setup script for Smart Survey Analytics with pgvector
Creates tables, loads CSV data, and generates embeddings
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from openai import OpenAI
import numpy as np

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

# Embedding dimension for text-embedding-3-small
EMBEDDING_DIM = 1536

def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def create_tables():
    """Create survey table with vector columns"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Drop existing table if exists
    cur.execute("DROP TABLE IF EXISTS survey CASCADE;")
    
    # Create survey table with all columns from CSV
    create_sql = """
    CREATE TABLE survey (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP,
        student_name TEXT,
        roll_number TEXT,
        school_name TEXT,
        class TEXT,
        last_year_percentage NUMERIC,
        study_time TEXT,
        toughest_subject TEXT,
        subject_group TEXT,
        
        -- Teacher ratings by subject (stored as text)
        teacher_rating_excellent TEXT,
        teacher_rating_very_good TEXT,
        teacher_rating_good TEXT,
        teacher_rating_average TEXT,
        teacher_rating_poor TEXT,
        
        -- Core satisfaction metrics
        teaching_quality TEXT,
        teacher_support TEXT,
        learning_goal_method TEXT,
        real_world_examples TEXT,
        interactive_classroom TEXT,
        
        -- Facilities
        lab_satisfaction TEXT,
        extracurricular_resources TEXT,
        school_events TEXT,
        transport_satisfaction TEXT,
        career_guidance TEXT,
        
        -- Environment
        bullying_resolution TEXT,
        fee_behaviour TEXT,
        exam_fairness TEXT,
        wellness_support TEXT,
        competitive_exam_preparedness TEXT,
        
        -- Overall
        overall_teaching_satisfaction TEXT,
        recommendation_score INTEGER,
        
        -- Open-ended feedback (text)
        teacher_feedback TEXT,
        school_feedback TEXT,
        school_suggestions TEXT,
        
        -- Vector embeddings for semantic search
        teacher_feedback_embedding vector(1536),
        school_feedback_embedding vector(1536),
        school_suggestions_embedding vector(1536)
    );
    
    -- Create indexes for vector similarity search
    CREATE INDEX ON survey USING ivfflat (teacher_feedback_embedding vector_cosine_ops) WITH (lists = 100);
    CREATE INDEX ON survey USING ivfflat (school_feedback_embedding vector_cosine_ops) WITH (lists = 100);
    CREATE INDEX ON survey USING ivfflat (school_suggestions_embedding vector_cosine_ops) WITH (lists = 100);
    """
    
    cur.execute(create_sql)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tables created successfully")

def is_valid_feedback(text):
    """Check if text is valid for embedding generation"""
    if not text or pd.isna(text):
        return False
    
    text = str(text).strip().lower()
    
    # Minimum length check
    if len(text) < 15:
        return False
    
    # Check alphabetic ratio
    alpha_count = sum(1 for c in text if c.isalpha())
    if alpha_count < len(text) * 0.5:
        return False
    
    # Generic/invalid responses
    invalid_responses = [
        'no concerns', 'none', 'na', 'n/a', 'nothing', 'ok', 'okay', 'good',
        'fine', 'nice', 'no', 'yes', 'no comment', 'no comments', 'nil',
        'everything good', 'all good', 'no issues', 'no suggestions'
    ]
    
    if text in invalid_responses:
        return False
    
    return True

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
        print(f"Embedding error: {e}")
        return None

def load_csv_to_db(csv_path="school_survey_1500.csv"):
    """Load CSV data into PostgreSQL and generate embeddings"""
    print(f"📂 Loading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Map CSV columns to database columns
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
    cur = conn.cursor()
    
    total_rows = len(df)
    embeddings_generated = 0
    
    print(f"📊 Processing {total_rows} rows...")
    
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"  Processing row {idx}/{total_rows}...")
        
        # Extract values
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
        
        # Generate embeddings for open-ended feedback
        teacher_emb = generate_embedding(values.get('teacher_feedback'))
        school_emb = generate_embedding(values.get('school_feedback'))
        suggestions_emb = generate_embedding(values.get('school_suggestions'))
        
        if teacher_emb:
            embeddings_generated += 1
        if school_emb:
            embeddings_generated += 1
        if suggestions_emb:
            embeddings_generated += 1
        
        # Insert row (36 columns total)
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
        
        cur.execute(insert_sql, (
            values.get('timestamp'), values.get('student_name'), values.get('roll_number'),
            values.get('school_name'), values.get('class'), values.get('last_year_percentage'),
            values.get('study_time'),
            values.get('toughest_subject'), values.get('subject_group'),
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
    cur.close()
    conn.close()
    
    print(f"✅ Loaded {total_rows} rows into database")
    print(f"✅ Generated {embeddings_generated} embeddings for valid feedback")

def verify_setup():
    """Verify database setup"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Count rows
    cur.execute("SELECT COUNT(*) FROM survey;")
    total = cur.fetchone()[0]
    
    # Count embeddings
    cur.execute("SELECT COUNT(*) FROM survey WHERE teacher_feedback_embedding IS NOT NULL;")
    teacher_emb = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM survey WHERE school_feedback_embedding IS NOT NULL;")
    school_emb = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM survey WHERE school_suggestions_embedding IS NOT NULL;")
    suggestions_emb = cur.fetchone()[0]
    
    # Verify Roll Number + School Name uniqueness
    cur.execute("""
        SELECT roll_number, school_name, COUNT(*) as cnt 
        FROM survey 
        GROUP BY roll_number, school_name 
        HAVING COUNT(*) > 1
    """)
    duplicates = cur.fetchall()
    
    # Count by school
    cur.execute("SELECT school_name, COUNT(*) FROM survey GROUP BY school_name ORDER BY school_name;")
    schools = cur.fetchall()
    
    print("\n📊 Database Status:")
    print(f"   Total rows: {total}")
    print(f"   Teacher feedback embeddings: {teacher_emb}")
    print(f"   School feedback embeddings: {school_emb}")
    print(f"   School suggestions embeddings: {suggestions_emb}")
    print(f"\n🏫 Schools Distribution:")
    for school_name, count in schools:
        print(f"   {school_name}: {count} students")
    
    if len(duplicates) == 0:
        print(f"\n✅ All Roll Number + School Name combinations are unique!")
    else:
        print(f"\n⚠️  Warning: Found {len(duplicates)} duplicate Roll Number + School Name combinations:")
        for roll_num, school, cnt in duplicates:
            print(f"   {roll_num} + {school}: {cnt} occurrences")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("🚀 Setting up Smart Survey Database...")
    create_tables()
    load_csv_to_db()
    verify_setup()
    print("\n✅ Database setup complete!")
