"""
load_data.py
Load CSV data into PostgreSQL - simplified version without embeddings initially
"""

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Database configuration - use Unix socket
DB_CONFIG = {
    "database": "smart_survey",
    "user": "postgres",
    "host": "/var/run/postgresql",
    "port": 5433
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def load_csv_basic():
    """Load CSV data without embeddings first"""
    print("📂 Loading CSV: school_survey_1500.csv")
    df = pd.read_csv("school_survey_1500.csv")
    
    # Map CSV columns to database columns
    column_mapping = {
        'Timestamp': 'timestamp',
        'Your name': 'student_name',
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
    print(f"📊 Processing {total_rows} rows...")
    
    for idx, row in df.iterrows():
        if idx % 300 == 0:
            print(f"  Processing row {idx}/{total_rows}...")
        
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
        
        insert_sql = """
        INSERT INTO survey (
            timestamp, student_name, school_name, class, last_year_percentage,
            study_time, toughest_subject, subject_group,
            teacher_rating_excellent, teacher_rating_very_good, teacher_rating_good,
            teacher_rating_average, teacher_rating_poor,
            teacher_support, learning_goal_method, real_world_examples, interactive_classroom,
            teacher_feedback, lab_satisfaction, extracurricular_resources, school_events,
            transport_satisfaction, career_guidance, school_feedback,
            bullying_resolution, fee_behaviour, exam_fairness, wellness_support,
            competitive_exam_preparedness, overall_teaching_satisfaction, recommendation_score,
            school_suggestions
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        cur.execute(insert_sql, (
            values.get('timestamp'), values.get('student_name'), values.get('school_name'),
            values.get('class'), values.get('last_year_percentage'), values.get('study_time'),
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
            values.get('recommendation_score'), values.get('school_suggestions')
        ))
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Loaded {total_rows} rows into database")

def verify_data():
    """Verify data loaded"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM survey;")
    total = cur.fetchone()[0]
    print(f"\n📊 Database has {total} rows")
    cur.close()
    conn.close()

if __name__ == "__main__":
    load_csv_basic()
    verify_data()
