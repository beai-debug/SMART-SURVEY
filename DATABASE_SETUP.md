# Database Setup Guide

This guide explains how to set up the Smart Survey database with pre-existing data and embeddings.

## Overview

The project uses **PostgreSQL** with the **pgvector** extension for semantic search capabilities. The database contains:
- 1,500 survey responses
- Pre-generated embeddings for text feedback fields (using OpenAI's text-embedding-3-small model)
- Vector indexes for fast similarity search

## Where is the Data Stored?

Your SQL data is stored in:
- **Database Type:** PostgreSQL 16
- **Database Name:** `smart_survey`
- **Location:** PostgreSQL server (Unix socket at `/var/run/postgresql`)
- **Table:** `survey` table with 36 columns including vector embeddings
- **Backup File:** `smart_survey_dump.sql` (33MB) - includes all data and embeddings

---

## Quick Setup (Recommended for GitHub Codespaces)

### Step 1: Activate Virtual Environment

```bash
source .venv/bin/activate
```

### Step 2: Start PostgreSQL

```bash
sudo service postgresql start
```

### Step 3: Install pgvector Extension

```bash
sudo apt-get update
sudo apt-get install -y postgresql-16-pgvector
```

### Step 4: Create Database and Enable pgvector

```bash
# Create the database (uses sudo su - postgres to avoid password prompt)
sudo su - postgres -c "psql -c 'CREATE DATABASE smart_survey;'"

# Enable pgvector extension
sudo su - postgres -c "psql -d smart_survey -c 'CREATE EXTENSION IF NOT EXISTS vector;'"

# Set password for postgres user (to match .env configuration)
sudo su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'smartsurvey';\""
```

### Step 5: Configure pg_hba.conf for Password Authentication

```bash
# Add password authentication rules
sudo bash -c "echo 'host    all             postgres        127.0.0.1/32            md5' >> /etc/postgresql/16/main/pg_hba.conf"
sudo bash -c "echo 'host    all             postgres        ::1/128                 md5' >> /etc/postgresql/16/main/pg_hba.conf"

# Reload PostgreSQL to apply changes
sudo service postgresql reload
```

### Step 6: Verify Connection

```bash
# Test connection with password
.venv/bin/python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', database='smart_survey', user='postgres', password='smartsurvey')
cur = conn.cursor()
cur.execute('SELECT version();')
print('PostgreSQL:', cur.fetchone()[0][:50])
cur.execute(\"SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';\")
result = cur.fetchone()
print(f'pgvector: {result[0]} v{result[1]}' if result else 'pgvector NOT found')
conn.close()
print('✅ Connection successful!')
"
```

### Step 7: Restore from Dump (Optional - if dump file exists)

```bash
# Restore the database from the dump file (includes all data + embeddings)
PGPASSWORD=smartsurvey psql -h localhost -U postgres -d smart_survey < smart_survey_dump.sql
```

### Step 8: Or Load Fresh Data

```bash
# Run the database setup script to create tables and load data
.venv/bin/python db_setup.py
```

---

## One-Liner Setup Script

For convenience, you can run all setup steps at once:

```bash
source .venv/bin/activate && \
sudo service postgresql start && \
sudo apt-get update && sudo apt-get install -y postgresql-16-pgvector && \
sudo su - postgres -c "psql -c 'CREATE DATABASE smart_survey;'" 2>/dev/null || true && \
sudo su - postgres -c "psql -d smart_survey -c 'CREATE EXTENSION IF NOT EXISTS vector;'" && \
sudo su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'smartsurvey';\"" && \
sudo bash -c "echo 'host    all             postgres        127.0.0.1/32            md5' >> /etc/postgresql/16/main/pg_hba.conf" && \
sudo bash -c "echo 'host    all             postgres        ::1/128                 md5' >> /etc/postgresql/16/main/pg_hba.conf" && \
sudo service postgresql reload && \
echo "✅ Database setup complete!"
```

---

## Environment Configuration

### Step 1: Copy Environment File

```bash
cp .env.example .env
```

### Step 2: Edit .env File

```bash
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_NAME=smart_survey
DB_USER=postgres
DB_PASSWORD=smartsurvey

# OpenAI API Configuration
OPENAI_API_KEY=sk-your-actual-openai-key-here
MODEL_NAME=gpt-4o

# Google API (optional)
GOOGLE_API_KEY=your-actual-google-key-here
```

---

## Alternative: Full Setup from Scratch

If you want to regenerate everything from the CSV file:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the database setup script (will regenerate embeddings - costs API credits!)
.venv/bin/python db_setup.py
```

⚠️ **Warning:** This will make ~1,500+ API calls to OpenAI for embedding generation and may cost $0.50-$1.00.

---

## Database Schema

The `survey` table includes:
- Student demographics (name, roll_number, school_name, class, etc.)
- Academic metrics (last_year_percentage, study_time, toughest_subject)
- Teacher ratings (excellent, very_good, good, average, poor)
- Satisfaction metrics (teaching_quality, lab_satisfaction, transport_satisfaction, etc.)
- Open-ended feedback (teacher_feedback, school_feedback, school_suggestions)
- **Vector embeddings** (teacher_feedback_embedding, school_feedback_embedding, school_suggestions_embedding)

---

## Troubleshooting

### Issue: "sudo: a password is required"
**Solution:** Use `sudo su - postgres -c "command"` instead of `sudo -u postgres command`

### Issue: "relation does not exist"
**Solution:** Make sure you've restored the dump file or run `db_setup.py`

### Issue: "extension vector does not exist"
**Solution:** Install pgvector extension: `sudo apt-get install postgresql-16-pgvector`

### Issue: Connection refused
**Solution:** Check if PostgreSQL is running: `sudo service postgresql status`

### Issue: "password authentication failed"
**Solution:** 
1. Set the password: `sudo su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'smartsurvey';\""`
2. Update pg_hba.conf and reload PostgreSQL

### Issue: "Peer authentication failed"
**Solution:** Add md5 authentication to pg_hba.conf and reload PostgreSQL

---

## Testing the Setup

Run the test scripts to verify everything works:

```bash
# Activate virtual environment first
source .venv/bin/activate

# Test the survey copilot
.venv/bin/python test_survey_copilot.py

# Test the API
.venv/bin/python test_api.py
```

---

## Notes

- The database dump is included in the repository so you **don't need to regenerate embeddings**
- Your `.env` file is gitignored to protect API keys
- The `school_survey_1500.csv` file is also included as a backup data source
- Always run Python scripts using `.venv/bin/python` to ensure correct environment
- Temporary SQL files (*_local.sql, *_temp.sql) are ignored by git

## Need Help?

If you encounter issues, check:
1. PostgreSQL is running and accessible: `sudo service postgresql status`
2. pgvector extension is properly installed: `dpkg -l | grep pgvector`
3. Your `.env` file has correct API keys (copy from `.env.example`)
4. The database was restored successfully from the dump file
5. You're running commands inside the virtual environment: `source .venv/bin/activate`
