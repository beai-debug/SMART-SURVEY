"""
generate_embeddings.py
Generate embeddings for open-ended feedback columns using OpenAI
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Database configuration
DB_CONFIG = {
    "database": "smart_survey",
    "user": "postgres",
    "host": "/var/run/postgresql",
    "port": 5433
}

# OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def is_valid_feedback(text):
    """Check if text is valid for embedding generation"""
    if not text:
        return False
    
    text_original = str(text).strip()
    text_lower = text_original.lower()
    
    # Long feedback (>50 chars) is always valid - these are our detailed responses
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
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=str(text)
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def generate_all_embeddings():
    """Generate embeddings for all valid feedback entries"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get rows with feedback that needs embedding
    cur.execute("""
        SELECT id, teacher_feedback, school_feedback, school_suggestions
        FROM survey
        WHERE teacher_feedback_embedding IS NULL 
           OR school_feedback_embedding IS NULL
           OR school_suggestions_embedding IS NULL
    """)
    
    rows = cur.fetchall()
    print(f"📊 Processing {len(rows)} rows for embeddings...")
    
    update_cur = conn.cursor()
    embeddings_count = 0
    
    for idx, row in enumerate(rows):
        if idx % 100 == 0:
            print(f"  Processing row {idx}/{len(rows)}...")
            conn.commit()  # Commit periodically
        
        updates = []
        params = []
        
        # Teacher feedback
        if is_valid_feedback(row['teacher_feedback']):
            emb = generate_embedding(row['teacher_feedback'])
            if emb:
                updates.append("teacher_feedback_embedding = %s::vector")
                params.append(emb)
                embeddings_count += 1
        
        # School feedback
        if is_valid_feedback(row['school_feedback']):
            emb = generate_embedding(row['school_feedback'])
            if emb:
                updates.append("school_feedback_embedding = %s::vector")
                params.append(emb)
                embeddings_count += 1
        
        # School suggestions
        if is_valid_feedback(row['school_suggestions']):
            emb = generate_embedding(row['school_suggestions'])
            if emb:
                updates.append("school_suggestions_embedding = %s::vector")
                params.append(emb)
                embeddings_count += 1
        
        if updates:
            params.append(row['id'])
            sql = f"UPDATE survey SET {', '.join(updates)} WHERE id = %s"
            update_cur.execute(sql, params)
    
    conn.commit()
    cur.close()
    update_cur.close()
    conn.close()
    
    print(f"✅ Generated {embeddings_count} embeddings")

def verify_embeddings():
    """Verify embedding counts"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM survey WHERE teacher_feedback_embedding IS NOT NULL;")
    teacher = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM survey WHERE school_feedback_embedding IS NOT NULL;")
    school = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM survey WHERE school_suggestions_embedding IS NOT NULL;")
    suggestions = cur.fetchone()[0]
    
    print(f"\n📊 Embedding Status:")
    print(f"   Teacher feedback embeddings: {teacher}")
    print(f"   School feedback embeddings: {school}")
    print(f"   School suggestions embeddings: {suggestions}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("🚀 Generating embeddings...")
    generate_all_embeddings()
    verify_embeddings()
