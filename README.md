# 🎓 SMART-SURVEY: AI-Powered School Survey Analytics

An intelligent survey analytics system that combines **SQL analytics** (for numbers) with **semantic search** (for understanding feedback) to answer complex questions about school survey data.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![pgvector](https://img.shields.io/badge/pgvector-0.5-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-orange)

---

## 🚀 What Does This Project Do?

Imagine you have survey responses from 1500 students. You want to ask questions like:

- ❓ **"What percentage of students are dissatisfied with transport?"** → Needs numbers (SQL)
- ❓ **"What do students complain about teachers?"** → Needs understanding text (Semantic Search)
- ❓ **"Why is competitive exam preparedness rated low?"** → Needs BOTH numbers AND reasons

This system automatically:
1. **Understands your question** (Is it about numbers? Opinions? Or both?)
2. **Runs the right analysis** (SQL for numbers, vector search for opinions)
3. **Generates beautiful charts** for QUANT/MIXED queries
4. **Returns human-readable insights** with full student metadata

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Technical Details](#-technical-details)
- [Testing](#-testing)
- [Chart Generation](#-chart-generation)
- [Why Not Graph RAG?](#-why-not-graph-rag)

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 16 with pgvector extension
- OpenAI API key

### go inside .venv

```bash
source .venv/bin/activate   
```

### 1. Clone and Install

```bash
git clone https://github.com/Jatin2832003/SMART-SURVEY.git
cd SMART-SURVEY
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-key-here
# MODEL_NAME=gpt-4o
```

### 3. Set Up Database

```bash
# Start PostgreSQL and create database
bash setup_db.sh

# Or manually:
sudo service postgresql start
python db_setup.py
```

### 4. Load Sample Data

```bash
# Generate sample survey data (1500 rows with 25% detailed feedback)
python generate_csv.py

# Load data into PostgreSQL
python load_data.py

# Generate embeddings for semantic search
python generate_embeddings.py
```

### 5. Run the Copilot

```bash
python survey_copilot.py
```

Example session:
```
🎓 SMART SURVEY ANALYTICS COPILOT
==================================

📝 Your question: Why is competitive exam preparedness rated low?

🔍 Query: Why is competitive exam preparedness rated low?
📌 Intent: MIXED

📊 **Metrics** (n=1500)
• Disagree: 54.1% (333 students)
• Strongly disagree: 45.9% (283 students)

💬 **Feedback Insights** (10 relevant responses)
The primary issue is the inadequacy of library resources. Students express
the need to rely on external sources due to outdated reference books...
```

---

## 🔍 How It Works

### The 3-Step Process

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. CLASSIFY    │ ──▶ │   2. EXECUTE    │ ──▶ │   3. FORMAT     │
│    INTENT       │     │    ANALYSIS     │     │    RESPONSE     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
   GPT-4 decides          SQL or Vector           GPT-4 creates
   QUANT/QUAL/MIXED       Search runs           readable answer
                                │
                                ▼
                    ┌─────────────────┐
                    │   4. GENERATE   │
                    │     CHARTS      │
                    └─────────────────┘
                            │
                    Seaborn/Matplotlib
                    saves to smart_outputs/
```

### Intent Types

| Intent | What User Wants | Example Question | Method | Charts |
|--------|-----------------|------------------|--------|--------|
| **QUANT** | Numbers, percentages, counts | "What % are dissatisfied?" | SQL Query | ✅ Yes |
| **QUAL** | Opinions, themes, feedback | "What do students complain about?" | Vector Search | ❌ No |
| **MIXED** | Numbers + explanations | "Why is satisfaction low?" | SQL + Vector | ✅ Yes |

---

## 📁 Project Structure

```
SMART-SURVEY/
├── survey_copilot.py       # 🎯 Main entry point - the AI copilot
├── generate_csv.py         # 📊 Generate sample survey data (25% long feedback)
├── load_data.py            # 📥 Load CSV data into PostgreSQL
├── generate_embeddings.py  # 🔢 Create vector embeddings
├── db_setup.py             # 🗄️ Database schema setup
├── test_survey_copilot.py  # 🧪 Test suite with charts & metadata output
├── graph.py                # 📈 Visualization utilities
├── requirements.txt        # 📦 Python dependencies
├── .env                    # 🔐 Environment variables (API keys)
├── README.md               # 📖 This file
├── ARCHITECTURE.md         # 📖 Detailed architecture documentation
└── smart_outputs/          # 📊 Generated charts saved here
```

---

## 🛠️ Technical Details

### Models Used

| Component | Model | Why This Model? |
|-----------|-------|-----------------|
| **Intent Classification** | GPT-4o | Best at understanding natural language intent |
| **SQL Generation** | GPT-4o | Excellent at generating accurate SQL from text |
| **Embeddings** | text-embedding-3-small | Fast, affordable, 1536 dimensions |
| **Response Formatting** | GPT-4o | Creates clear, human-readable summaries |
| **Chart Generation** | Seaborn + Matplotlib | Beautiful, customizable visualizations |

### Database Schema

```sql
CREATE TABLE survey (
    id SERIAL PRIMARY KEY,
    
    -- Student Info
    student_name TEXT,
    school_name TEXT,
    class TEXT,  -- '6 th', '7 th', ... '12th'
    subject_group TEXT,  -- 'Maths', 'Biology', 'IT/CS', 'Commerce'
    study_time TEXT,
    
    -- Satisfaction Ratings (Likert scales)
    teacher_support TEXT,
    transport_satisfaction TEXT,
    career_guidance TEXT,
    competitive_exam_preparedness TEXT,
    overall_teaching_satisfaction TEXT,
    recommendation_score INTEGER,
    -- ... more rating columns
    
    -- Open-ended Feedback (TEXT)
    teacher_feedback TEXT,
    school_feedback TEXT,
    school_suggestions TEXT,
    
    -- Vector Embeddings (for semantic search)
    teacher_feedback_embedding vector(1536),
    school_feedback_embedding vector(1536),
    school_suggestions_embedding vector(1536)
);
```

### Vector Search with Full Metadata

```sql
-- Find similar feedback with ALL student metadata
SELECT 
    id, student_name, school_name, class, subject_group,
    study_time, teacher_support, transport_satisfaction,
    career_guidance, competitive_exam_preparedness,
    overall_teaching_satisfaction, recommendation_score,
    feedback,
    1 - (embedding <=> query_embedding) as similarity
FROM survey
WHERE embedding IS NOT NULL
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

---

## 📊 Chart Generation

Charts are automatically generated for **QUANT** and **MIXED** queries using Seaborn/Matplotlib:

### Features
- **Auto-detection** of chart type based on data structure
- **Beautiful styling** with husl color palette
- **Value labels** on bars for easy reading
- **Saved to `smart_outputs/`** folder with timestamps

### Chart Types Generated

| Data Structure | Chart Type |
|----------------|------------|
| Single categorical + numeric | Horizontal bar chart |
| Two categorical + percentage | Grouped bar chart |
| Multiple numeric columns | Scatter plot |
| Distribution data | Stacked/grouped bars |

### Example Charts

```
smart_outputs/
├── chart_What is the overall teaching s_20260131_133441.png
├── chart_Show transport satisfaction br_20260131_133446.png
├── chart_Compare lab satisfaction betwe_20260131_133458.png
├── chart_Why is competitive exam prepar_20260131_133520.png
└── chart_Why are students dissatisfied _20260131_133530.png
```

---

## 🧪 Testing

Run the test suite to verify everything works:

```bash
python test_survey_copilot.py
```

This tests 10 queries (4 QUANT, 3 QUAL, 3 MIXED) and generates:

### Test Output
```
🧪 Running Survey Copilot Tests...
============================================================

[1/10] Testing: What is the overall teaching satisfaction...
    📌 Intent: QUANT
    📊 Chart saved: smart_outputs/chart_What is the overall teaching s_20260131.png
    ✅ Success

[5/10] Testing: What do students complain about regarding teachers...
    📌 Intent: QUAL
    ✅ Success

[8/10] Testing: Why is competitive exam preparedness rated low?...
    📌 Intent: MIXED
    📊 Chart saved: smart_outputs/chart_Why is competitive exam prepar_20260131.png
    ✅ Success

============================================================
✅ Results saved to: test_results_20260131_133829.md
📊 Total queries: 10
✅ Successful: 10
❌ Failed: 0
📈 Charts generated: 7
```

### Markdown Report Features

| Feature | Description |
|---------|-------------|
| **Charts** | Auto-generated PNG charts embedded in markdown |
| **Metadata Table** | Full student info (name, class, subject, satisfaction) |
| **Expandable Details** | `<details>` sections with complete metadata per result |
| **Summary Stats** | Success rates by intent type |
| **Charts Gallery** | List of all generated chart files |

### Sample Metadata Table in Output

```markdown
| # | Student | Class | Subject Group | Satisfaction | Study Time | Similarity |
|---|---------|-------|---------------|--------------|------------|------------|
| 1 | Kavita Tripathi | 12th | Not Applicable | Extremely dissatisfied | 3-4 Hrs | 0.5154 |
| 2 | Suresh Gupta | 10 th | Commerce | Highly satisfied | More than 4 Hrs | 0.5154 |
| 3 | Sanjay Sharma | 9 th | Biology | Extremely dissatisfied | 2-3 Hrs | 0.5154 |
```

---

## 🤔 Why Not Graph RAG?

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed explanation, but here's the summary:

### Graph RAG is Great For:
- Documents with entities and relationships (people, companies, events)
- Knowledge bases where connections matter ("Who knows whom?")
- Research papers, news articles, corporate documents

### Survey Data is Different:

| Aspect | Graph RAG | Survey Data |
|--------|-----------|-------------|
| **Structure** | Entities + Relationships | Rows + Columns |
| **Queries** | "Find connected entities" | "Count/Average/Compare" |
| **Relationships** | Complex, multi-hop | Flat, tabular |
| **Aggregations** | Hard | Natural (SQL) |

### Our Hybrid Approach Works Better:

```
Survey Question Types:
─────────────────────
"What % dissatisfied?"     → SQL is perfect ✅
"What do students say?"    → Vector search ✅
"Why are scores low?"      → SQL + Vector ✅

Graph RAG would need:
─────────────────────
- Extract entities from feedback (overkill)
- Build knowledge graph (unnecessary)
- Query graph + aggregate (SQL is simpler)
```

**Bottom Line:** SQL + Vector Search is simpler, faster, and more accurate for survey analytics than Graph RAG.

---

## 📊 Sample Queries You Can Ask

### Quantitative (QUANT) - With Charts
- "What is the overall teaching satisfaction distribution?"
- "Show transport satisfaction breakdown by class"
- "What percentage of students study more than 4 hours?"
- "Compare lab satisfaction between Maths and Biology groups"

### Qualitative (QUAL) - With Full Metadata
- "What do students complain about regarding teachers?"
- "What suggestions do students have for the school?"
- "What are common issues with school facilities?"

### Mixed (QUANT + QUAL) - Charts + Metadata
- "Why is competitive exam preparedness rated low?"
- "Why are students dissatisfied with career guidance?"
- "What are the reasons behind low transport satisfaction?"

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-api-key-here
MODEL_NAME=gpt-4o  # or gpt-4-turbo, gpt-3.5-turbo

# Database Configuration (optional - defaults in code)
DB_NAME=smart_survey
DB_USER=postgres
DB_HOST=/var/run/postgresql
DB_PORT=5433
```

### Customizing Feedback Templates

Edit `generate_csv.py` to add your own long feedback templates (25% of data):

```python
LONG_TEACHER_FEEDBACK = [
    "Your detailed feedback template here...",
    # Add more templates
]
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Query Response Time | 2-5 seconds |
| Embedding Generation | ~100 rows/minute |
| Chart Generation | ~1 second per chart |
| Database Size | ~50MB for 1500 rows with embeddings |
| Test Success Rate | 100% (10/10 queries) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 and embeddings API
- PostgreSQL and pgvector team
- Seaborn and Matplotlib for beautiful charts
- All contributors and testers

---

**Made with ❤️ for better school analytics**
