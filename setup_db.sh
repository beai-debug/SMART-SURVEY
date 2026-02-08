#!/bin/bash
# Setup script for Smart Survey Database
# Run with: sudo -u postgres bash setup_db.sh

cd /workspaces/SMART-SURVEY

# Create tables
psql -d smart_survey << 'EOSQL'
DROP TABLE IF EXISTS survey CASCADE;

CREATE TABLE survey (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    student_name TEXT,
    school_name TEXT,
    class TEXT,
    last_year_percentage NUMERIC,
    study_time TEXT,
    toughest_subject TEXT,
    subject_group TEXT,
    teacher_rating_excellent TEXT,
    teacher_rating_very_good TEXT,
    teacher_rating_good TEXT,
    teacher_rating_average TEXT,
    teacher_rating_poor TEXT,
    teaching_quality TEXT,
    teacher_support TEXT,
    learning_goal_method TEXT,
    real_world_examples TEXT,
    interactive_classroom TEXT,
    lab_satisfaction TEXT,
    extracurricular_resources TEXT,
    school_events TEXT,
    transport_satisfaction TEXT,
    career_guidance TEXT,
    bullying_resolution TEXT,
    fee_behaviour TEXT,
    exam_fairness TEXT,
    wellness_support TEXT,
    competitive_exam_preparedness TEXT,
    overall_teaching_satisfaction TEXT,
    recommendation_score INTEGER,
    teacher_feedback TEXT,
    school_feedback TEXT,
    school_suggestions TEXT,
    teacher_feedback_embedding vector(1536),
    school_feedback_embedding vector(1536),
    school_suggestions_embedding vector(1536)
);

CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

echo "✅ Tables created"
