-- Load CSV data into survey table using COPY command

-- First, truncate existing data
TRUNCATE TABLE survey;

-- Create a temp table matching CSV structure
DROP TABLE IF EXISTS survey_import;
CREATE TEMP TABLE survey_import (
    ts TEXT,
    name TEXT,
    school TEXT,
    class TEXT,
    percentage TEXT,
    study_time TEXT,
    toughest_subject TEXT,
    subject_group TEXT,
    rating_excellent TEXT,
    rating_very_good TEXT,
    rating_good TEXT,
    rating_average TEXT,
    rating_poor TEXT,
    teacher_support TEXT,
    learning_goal TEXT,
    real_world TEXT,
    interactive TEXT,
    teacher_feedback TEXT,
    lab_satisfaction TEXT,
    extracurricular TEXT,
    school_events TEXT,
    transport TEXT,
    career_guidance TEXT,
    school_feedback TEXT,
    bullying TEXT,
    fee TEXT,
    exam_fairness TEXT,
    wellness TEXT,
    competitive TEXT,
    overall_teaching TEXT,
    recommend TEXT,
    school_suggestions TEXT
);

-- Copy from CSV
\copy survey_import FROM '/workspaces/SMART-SURVEY/school_survey_1500.csv' WITH CSV HEADER;

-- Insert into survey table with proper type conversions
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
)
SELECT 
    TO_TIMESTAMP(ts, 'DD/MM/YYYY HH24:MI:SS'),
    name,
    school,
    class,
    CAST(NULLIF(percentage, '') AS NUMERIC),
    study_time,
    toughest_subject,
    subject_group,
    rating_excellent,
    rating_very_good,
    rating_good,
    rating_average,
    rating_poor,
    teacher_support,
    learning_goal,
    real_world,
    interactive,
    teacher_feedback,
    lab_satisfaction,
    extracurricular,
    school_events,
    transport,
    career_guidance,
    school_feedback,
    bullying,
    fee,
    exam_fairness,
    wellness,
    competitive,
    overall_teaching,
    CAST(NULLIF(recommend, '') AS INTEGER),
    school_suggestions
FROM survey_import;

-- Verify
SELECT COUNT(*) as total_rows FROM survey;
SELECT class, COUNT(*) as count FROM survey GROUP BY class ORDER BY class;
