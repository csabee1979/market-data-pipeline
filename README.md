# Market Data Pipeline

An automated ETL pipeline for fetching, processing, and storing AI research papers from OpenAlex into a PostgreSQL database.

## Overview

This pipeline automates the collection and storage of AI research papers, providing a structured database for analysis and research. The system fetches papers from the OpenAlex API, filters them by AI relevance, and stores them in a normalized PostgreSQL database with comprehensive metadata.

## Features

- **Automated Paper Fetching**: Retrieves recent AI research papers from OpenAlex API
- **Intelligent Filtering**: Filters papers by AI relevance score and field classification
- **Robust Database Schema**: Normalized schema with papers, authors, and relationships
- **Batch Import**: Efficient bulk import with UPSERT strategy for deduplication
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Schema Management**: Automated database schema deployment

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**

- `pyalex==0.19` - OpenAlex API client
- `psycopg2-binary==2.9.9` - PostgreSQL adapter
- `python-dotenv==1.0.0` - Environment variable management
- `streamlit==1.51.0` - Web interface (optional)

### 2. Configure Database Credentials

Copy the `env.template` file to `.env` and add your database credentials:

```bash
# On Windows PowerShell
Copy-Item env.template .env

# On Linux/Mac
cp env.template .env
```

Edit `.env` and set your database password:

```
DB_PASSWORD=your_actual_password
```

### 3. Deploy Database Schema

Deploy the database schema before importing data:

```bash
python database/deploy_schema.py
```

This creates:

- 3 tables: `papers`, `authors`, `paper_authors`
- 39 indexes for optimized queries
- 1 trigger function for automatic metric updates
- 3 views for common queries

## Usage

### Fetch AI Research Papers

Fetch recent AI papers from OpenAlex (last 3 days):

```bash
python fetch_ai_papers.py
```

**What it does:**

- Searches for papers with "Artificial Intelligence" concept
- Filters by AI relevance score (≥ 0.7) OR AI field/subfield
- Saves filtered results to `temp/ai_papers_TIMESTAMP.json`
- Sorts papers by relevance score (highest first)

**Output:**

```
✅ Retrieved 1,234 AI-related paper(s) from API
✅ Filtered to 456 highly relevant AI paper(s)
   📊 Precision: 37.0%
   📊 Papers with AI field/subfield: 234
   📊 Papers with score ≥ 0.7: 222
💾 Saved 456 paper(s) to: temp/ai_papers_2025-11-14_13-04-35.json
```

### Import Papers to Database

Import papers from JSON file into the database:

```bash
python database/import_papers.py temp/ai_papers_TIMESTAMP.json
```

**Options:**

- `--log-dir`: Directory for log files (default: `logs`)
- `--batch-size`: Papers per batch (default: 1)

**What it does:**

- Transforms JSON data to database schema format
- Inserts/updates papers, authors, and relationships
- Uses UPSERT strategy to avoid duplicates
- Provides detailed statistics and logging

**Output:**

```
======================================================================
IMPORT SUMMARY
======================================================================
Papers:
  - Processed: 456
  - Inserted:  423
  - Updated:   33
  - Failed:    0

Authors:
  - Inserted:  1,234
  - Updated:   567
  - Failed:    0

Paper-Authors Relationships:
  - Inserted:  2,345
  - Updated:   123
  - Failed:    0

Duration: 45.67 seconds
======================================================================
```

### Test Database Connection

Verify your database connection:

```bash
# Quick test
python database/database.py

# Comprehensive test suite
python database/test_database.py
```

## Database Module

The `database` module provides utilities for connecting to PostgreSQL:

### Using in Your Code

```python
from database import get_connection, execute_query, verify_connection

# Method 1: Using context manager (recommended)
with get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE ai_relevance_score > 0.9")
    results = cursor.fetchall()

# Method 2: Using execute_query helper
results = execute_query("SELECT COUNT(*) FROM papers")

# Method 3: Verify connection
success, message = verify_connection()
print(message)
```

### Database Module Features

- **`DatabaseConfig`**: Loads credentials from `.env` file
- **`DatabaseConnection`**: Connection manager with context manager support
- **`get_connection()`**: Context manager for easy connection handling
- **`execute_query()`**: Helper function for executing queries
- **`verify_connection()`**: Test and verify database connectivity

### Connection Details

- **Host**: `ep-polished-moon-agsi4bae-pooler.c-2.eu-central-1.aws.neon.tech`
- **Database**: `neondb`
- **User**: `neondb_owner`
- **SSL Mode**: `require`

## Database Schema

### Tables

1. **`papers`**: Research paper metadata

   - Paper ID, DOI, title, publication info
   - Journal and publisher information
   - Open access status and URLs
   - Citation metrics (cited_by_count, FWCI)
   - Topics, concepts, and keywords
   - AI relevance score and flags

2. **`authors`**: Author information

   - Author ID, display name, ORCID
   - Primary institution and country
   - Automatically updated metrics (paper count, citations)

3. **`paper_authors`**: Many-to-many relationships
   - Paper-author associations
   - Author position and sequence
   - Institutional affiliations
   - Corresponding author flags

### Views

- **`paper_summary`**: Aggregated paper statistics
- **`author_summary`**: Author metrics and rankings
- **`recent_papers`**: Recently published papers

See `database/SCHEMA_SUMMARY.md` for detailed schema documentation.

## Project Structure

```
market-data-pipeline/
├── database/
│   ├── database.py          # Database connection utilities
│   ├── deploy_schema.py     # Schema deployment script
│   ├── import_papers.py     # Paper import ETL script
│   ├── schema.sql           # Database schema definition
│   ├── test_database.py     # Database connection tests
│   └── SCHEMA_SUMMARY.md    # Schema documentation
├── logs/                    # Import logs (timestamped)
├── temp/                    # Temporary JSON files
├── fetch_ai_papers.py       # OpenAlex API fetcher
├── requirements.txt         # Python dependencies
├── env.template             # Environment variable template
└── README.md               # This file
```

## Workflow

The typical workflow for the pipeline:

1. **Fetch Papers**: Run `fetch_ai_papers.py` to get recent AI papers
2. **Import to Database**: Run `import_papers.py` with the generated JSON file
3. **Analyze Data**: Query the database for insights and analysis

### Example Complete Workflow

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Fetch recent papers
python fetch_ai_papers.py

# Import to database (use the generated filename)
python database/import_papers.py temp/ai_papers_2025-11-14_13-04-35.json

# Check logs for details
type logs\import_papers_2025-11-14_13-05-46.log
```

## AI Relevance Scoring

Papers are scored based on multiple factors:

- **Keywords**: Direct AI terms (2.0x weight), ML/DL terms (1.5x weight)
- **Concepts**: AI concepts (2.0x weight), ML concepts (1.5x weight)
- **Topics**: AI field/subfield (0.9 score), CS field (0.5 score)

**Selection Criteria:**

- Papers with AI relevance score ≥ 0.7, OR
- Papers with "Artificial Intelligence" as field or subfield

## Logging

All import operations are logged to `logs/` directory with timestamps:

- **Console**: INFO level messages (progress, summary)
- **File**: DEBUG level messages (detailed operations, errors)

Log files include:

- Detailed transformation steps
- Database operations (inserts/updates)
- Error messages with stack traces
- Final statistics summary

## Troubleshooting

### Database Connection Issues

1. Check `.env` file exists and has correct credentials
2. Verify database is accessible from your network
3. Run `python database/test_database.py` for diagnostics

### Import Failures

1. Check log files in `logs/` directory for detailed errors
2. Verify JSON file format matches OpenAlex schema
3. Ensure database schema is deployed (`deploy_schema.py`)

### API Rate Limits

The fetcher includes automatic retry with exponential backoff:

- Max 10 retry attempts
- Initial delay: 1 second
- Exponential backoff multiplier: 2x

## Contributing

When adding new features:

1. Update the database schema in `database/schema.sql`
2. Redeploy schema using `deploy_schema.py`
3. Update transformation logic in `import_papers.py`
4. Add tests to verify functionality
5. Update this README with new features
