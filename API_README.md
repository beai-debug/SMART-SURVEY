# Smart Survey Analytics API

A comprehensive FastAPI application for managing and analyzing school survey data with AI-powered search capabilities.

## Features

- **Status Monitoring**: Get real-time database statistics with aggregations by school, class, and subject group
- **Data Loading**: Automatically load new survey responses from Google Sheets with duplicate detection
- **Delete Operations**: Three types of deletion endpoints with preview before delete
- **AI-Powered Search**: Intent-based search with quantitative SQL queries, qualitative semantic search, or mixed analysis
- **Vector Search**: Semantic similarity search using pgvector and OpenAI embeddings

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Make sure PostgreSQL with pgvector is running
# and the database is set up (run db_setup.py first)
```

## Running the API

```bash
# Start the server
python api.py

# Or using uvicorn directly
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Status Endpoint
**GET** `/status`

Get database status showing total records, records by school, and records by class with subject group breakdown.

**Response:**
```json
{
  "status": "success",
  "timestamp": "2026-02-08T12:00:00",
  "total_records": 1500,
  "embeddings": {
    "teacher_feedback": 450,
    "school_feedback": 520,
    "school_suggestions": 380
  },
  "by_school": [
    {"school_name": "JNV VARANASI", "count": 500},
    {"school_name": "KV DELHI", "count": 1000}
  ],
  "by_class": [
    {"class": "10 th", "count": 300}
  ],
  "by_class_with_subject_groups": {
    "10 th": {
      "total": 300,
      "subject_groups": {
        "Maths": 150,
        "Biology": 100,
        "Commerce": 50
      }
    }
  }
}
```

### 2. Load Recent Data
**POST** `/load-recent`

Load recent survey data from Google Sheets with automatic duplicate detection and embedding generation.

**Response:**
```json
{
  "status": "success",
  "timestamp": "2026-02-08T12:00:00",
  "sheets_url": "https://docs.google.com/...",
  "summary": {
    "total_rows_in_sheet": 1500,
    "records_added": 50,
    "records_skipped": 5,
    "records_without_embeddings": 10
  },
  "database_change": {
    "before": 1450,
    "after": 1500,
    "change": 50
  },
  "added_records": [...],
  "skipped_records": [...],
  "records_without_embeddings": [...]
}
```

### 3. Delete by Roll Number + School Name
**DELETE** `/delete/by-roll-school`

Delete specific student records by roll number and school name.

**Request Body:**
```json
{
  "roll_number": "300001",
  "school_name": "JNV VARANASI"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully deleted 1 record(s)",
  "deleted_count": 1,
  "deleted_records": [...]
}
```

### 4. Delete by School Name
**DELETE** `/delete/by-school`

Delete all records from a specific school.

**Request Body:**
```json
{
  "school_name": "JNV VARANASI"
}
```

### 5. Delete by Class (+ optional Subject Group)
**DELETE** `/delete/by-class`

Delete records by class and optionally filter by subject group.

**Request Body:**
```json
{
  "class_name": "10 th",
  "subject_group": "Maths"  // optional
}
```

### 6. Search with AI Intent Detection
**POST** `/search`

Intelligent search that automatically detects if your query needs:
- **QUANT**: Quantitative analysis (SQL aggregations, statistics)
- **QUAL**: Qualitative analysis (semantic search of feedback)
- **MIXED**: Combined analysis (metrics + reasoning from feedback)

**Request Body:**
```json
{
  "query": "Why are students dissatisfied with lab facilities?",
  "feedback_column": "school_feedback",  // optional: teacher_feedback, school_feedback, school_suggestions
  "limit": 10  // optional: max results for vector search
}
```

**Response:**
```json
{
  "status": "success",
  "intent": "MIXED",
  "final_response": "Human-readable analysis...",
  "retrieved_rows": {
    "type": "mixed",
    "quantitative": {
      "sample_size": 1500,
      "data": [...]
    },
    "qualitative": {
      "count": 10,
      "data": [...],
      "similarity_scores": [
        {
          "roll_number": "300001",
          "school_name": "JNV VARANASI",
          "similarity": 0.8543
        }
      ]
    }
  },
  "numbers_for_graph": {
    "mixed": {
      "quantitative": [...],
      "qualitative_count": 10
    },
    "quant": [...]
  },
  "sql_query": "SELECT ..."
}
```

## Query Examples

### Quantitative Queries (QUANT)
```bash
# Average satisfaction
"What is the average satisfaction with teaching?"

# Distributions
"Show transport satisfaction distribution by class"

# Comparisons
"Compare lab satisfaction between Math and Science students"

# Counts
"How many students are dissatisfied with career guidance?"
```

### Qualitative Queries (QUAL)
```bash
# Feedback themes
"What do students complain about regarding teachers?"

# Common issues
"What are common suggestions for school improvement?"

# Specific topics
"Show feedback about lab facilities"

# Sentiment analysis
"What feedback mentions bullying issues?"
```

### Mixed Queries (MIXED)
```bash
# Why questions
"Why is competitive exam preparedness rated low?"

# Reasoning
"What are the reasons behind transport dissatisfaction?"

# Explanations
"Explain why students rate teaching quality poorly"

# Combined insights
"What causes low recommendation scores?"
```

## Response Fields Explanation

### For Vector Search (QUAL/MIXED)
- **similarity_score**: Cosine similarity score (0-1), higher means more relevant
- **retrieved_rows.data**: Full database rows including all student information
- **final_response**: AI-generated summary of findings

### For Quantitative (QUANT)
- **numbers_for_graph.quant**: Array of aggregated data ready for visualization
- **sql_query**: Generated SQL query for transparency
- **sample_size**: Total records analyzed

### For Mixed (MIXED)
- **numbers_for_graph.mixed**: Both quantitative and qualitative data for graphs
- **combined_analysis**: LLM analysis connecting metrics with feedback

## Using with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Check status
response = requests.get(f"{BASE_URL}/status")
print(response.json())

# 2. Load recent data
response = requests.post(f"{BASE_URL}/load-recent")
print(response.json())

# 3. Delete by roll number and school
response = requests.delete(
    f"{BASE_URL}/delete/by-roll-school",
    json={
        "roll_number": "300001",
        "school_name": "JNV VARANASI"
    }
)
print(response.json())

# 4. Search with AI
response = requests.post(
    f"{BASE_URL}/search",
    json={
        "query": "Why are students dissatisfied with labs?",
        "limit": 10
    }
)
result = response.json()
print(f"Intent: {result['intent']}")
print(f"Response: {result['final_response']}")

# Access similarity scores for vector search
if result['intent'] in ['QUAL', 'MIXED']:
    for score in result['retrieved_rows']['qualitative']['similarity_scores']:
        print(f"Student {score['roll_number']}: {score['similarity']:.3f}")
```

## Using with cURL

```bash
# Status
curl http://localhost:8000/status

# Load recent data
curl -X POST http://localhost:8000/load-recent

# Delete by school
curl -X DELETE http://localhost:8000/delete/by-school \
  -H "Content-Type: application/json" \
  -d '{"school_name": "JNV VARANASI"}'

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What percentage of students are satisfied with teaching?", "limit": 10}'
```

## Graph Generation

The API returns data in `numbers_for_graph` field that's ready for visualization:

```python
import plotly.express as px
import pandas as pd

# For quantitative queries
response = requests.post(f"{BASE_URL}/search", json={
    "query": "Show satisfaction by class"
})
data = response.json()['numbers_for_graph']['quant']
df = pd.DataFrame(data)

# Create bar chart
fig = px.bar(df, x='class', y='percentage', title='Satisfaction by Class')
fig.show()

# For mixed queries - you get both metrics and feedback counts
mixed_data = response.json()['numbers_for_graph']['mixed']
quant_df = pd.DataFrame(mixed_data['quantitative'])
qual_count = mixed_data['qualitative_count']
```

## Error Handling

All endpoints return standard error responses:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

Common HTTP status codes:
- **200**: Success
- **500**: Internal server error (database, LLM, or processing error)

## Environment Variables

Required in `.env` file:
```bash
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o  # or gpt-4, gpt-3.5-turbo
```

## Database Schema

The API works with a PostgreSQL database containing:
- Survey responses with demographic and satisfaction data
- Vector embeddings for semantic search (teacher_feedback, school_feedback, school_suggestions)
- pgvector extension for similarity search

## Performance Notes

- Vector search is optimized with IVFFlat indexes
- Embedding generation uses OpenAI's text-embedding-3-small model
- Duplicate detection is based on (student_name, roll_number) combination
- SQL queries are generated dynamically with retry on failure

## Health Check

```bash
curl http://localhost:8000/health
```

Returns database connection status.

## Support

For issues or questions, refer to the main project README or check the interactive API documentation at `/docs`.
