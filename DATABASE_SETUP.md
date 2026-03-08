# Database Setup Guide

This guide explains how to set up the Smart Survey database with pre-existing data and embeddings.

## Overview

The project uses **PostgreSQL** with the **pgvector** extension for semantic search capabilities. The database contains:
- 1,500 survey responses
- Pre-generated embeddings for text feedback fields (using OpenAI's text-embedding-3-small model)
- Vector indexes for fast similarity search

## Where is the Data Stored?

Your SQL data is stored in:
- **Database Type:** PostgreSQL
- **Database Name:** `smart_survey`
- **Location:** PostgreSQL server (typically at `/var/lib/postgresql/data` or Unix socket at `/var/run/postgresql`)
- **Table:** `survey` table with 36 columns including vector embeddings
- **Backup File:** `smart_survey_dump.sql` (33MB) - includes all data and embeddings

## Quick Setup (Recommended)

Use the pre-generated database dump to avoid re-running expensive embedding generation:

### Step 1: Install PostgreSQL with pgvector

```bash
# Install PostgreSQL (if not already installed)
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Install pgvector extension
sudo apt-get install postgresql-15-pgvector
```

### Step 2: Start PostgreSQL

```bash
sudo service postgresql start
```

### Step 3: Create Database and Enable pgvector

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create the database
CREATE DATABASE smart_survey;

# Connect to the database
\c smart_survey

# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Exit psql
\q
```

### Step 4: Restore from Dump

```bash
# Restore the database from the dump file (includes all data + embeddings)
psql -h /var/run/postgresql -p 5433 -U postgres -d smart_survey < smart_survey_dump.sql
```

### Step 5: Verify Setup

```bash
# Check if data was loaded
psql -h /var/run/postgresql -p 5433 -U postgres -d smart_survey -c "SELECT COUNT(*) FROM survey;"

# Should return: 1500 rows
```

### Step 6: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Add your actual API keys:
```
OPENAI_API_KEY=sk-your-actual-openai-key-here
GOOGLE_API_KEY=your-actual-google-key-here
```

## Alternative: Full Setup from Scratch

If you want to regenerate everything from the CSV file:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the database setup script (will regenerate embeddings - costs API credits!)
python db_setup.py
```

⚠️ **Warning:** This will make ~1,500+ API calls to OpenAI for embedding generation and may cost $0.50-$1.00.

## Database Schema

The `survey` table includes:
- Student demographics (name, roll_number, school_name, class, etc.)
- Academic metrics (last_year_percentage, study_time, toughest_subject)
- Teacher ratings (excellent, very_good, good, average, poor)
- Satisfaction metrics (teaching_quality, lab_satisfaction, transport_satisfaction, etc.)
- Open-ended feedback (teacher_feedback, school_feedback, school_suggestions)
- **Vector embeddings** (teacher_feedback_embedding, school_feedback_embedding, school_suggestions_embedding)

## Troubleshooting

### Issue: "relation does not exist"
**Solution:** Make sure you've restored the dump file to the correct database.

### Issue: "extension vector does not exist"
**Solution:** Install pgvector extension: `sudo apt-get install postgresql-15-pgvector`

### Issue: Connection refused
**Solution:** Check if PostgreSQL is running: `sudo service postgresql status`

### Issue: Port 5433 not available
**Solution:** Check your PostgreSQL port in `/etc/postgresql/*/main/postgresql.conf`

## Testing the Setup

Run the test scripts to verify everything works:

```bash
# Test the survey copilot
python test_survey_copilot.py

# Test the API
python test_api.py
```

## Notes

- The database dump is included in the repository so you **don't need to regenerate embeddings**
- Your `.env` file is gitignored to protect API keys
- The `school_survey_1500.csv` file is also included as a backup data source
- Temporary SQL files (*_local.sql, *_temp.sql) are ignored by git

## Need Help?

If you encounter issues, check:
1. PostgreSQL is running and accessible
2. pgvector extension is properly installed
3. Your `.env` file has correct API keys (copy from `.env.example`)
4. The database was restored successfully from the dump file
