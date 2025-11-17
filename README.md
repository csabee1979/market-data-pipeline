# AI Research Papers Data Pipeline

An automated ETL pipeline for fetching, processing, and storing AI research papers from OpenAlex into a PostgreSQL database with comprehensive data quality validation.

## Overview

This pipeline automates the complete workflow for collecting, processing, and validating AI research papers data. The system provides both individual script execution and a consolidated pipeline that orchestrates the entire process from data fetching to quality validation.

## Features

### **📊 Data Pipeline**
- **Consolidated Pipeline**: Single command to run the complete workflow
- **Automated Paper Fetching**: Retrieves recent AI research papers from OpenAlex API
- **Intelligent Filtering**: Filters papers by AI relevance score and field classification
- **Robust Database Schema**: Normalized schema with papers, authors, and relationships
- **Data Quality Validation**: 18 comprehensive tests for data integrity
- **Batch Import**: Efficient bulk import with UPSERT strategy for deduplication
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Schema Management**: Automated database schema deployment
- **Configurable Execution**: YAML-based configuration for all pipeline stages

### **📈 Analytics Dashboard**
- **Interactive Streamlit Dashboard**: Web-based analytics interface
- **Multi-Page Navigation**: Overview, publications, authors, topics, geographic analysis
- **Real-time Visualizations**: Interactive charts with Plotly and modern UI
- **Search & Filtering**: Find papers by keywords, filter by date ranges
- **Performance Metrics**: Citation analysis, H-index rankings, impact metrics
- **Cross-Platform Launchers**: Easy-to-use scripts for Windows, Linux, Mac
- **Automated Setup**: One-click environment setup and dependency management
- **Professional Design**: Responsive layout with custom styling

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**

**Core Pipeline:**
- `pyalex==0.19` - OpenAlex API client
- `psycopg2-binary==2.9.9` - PostgreSQL adapter
- `python-dotenv==1.0.0` - Environment variable management
- `pyyaml>=6.0` - YAML configuration file parsing

**Analytics Dashboard:**
- `streamlit==1.51.0` - Web dashboard framework
- `plotly>=5.17.0` - Interactive visualizations
- `pandas>=2.0.0` - Data manipulation and analysis
- `numpy>=1.24.0` - Numerical computing
- `altair>=5.0.0` - Additional chart library
- `streamlit-aggrid>=0.3.0` - Enhanced data tables

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

### Analytics Dashboard (Quick Start)

Launch the interactive analytics dashboard to explore your data:

#### **Option A: Using Launcher Scripts (Recommended)**

**Windows (Command Prompt):**
```cmd
# Simply double-click or run:
run_dashboard.bat
```

**Windows (PowerShell):**
```powershell
# You may need to allow script execution first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run:
.\run_dashboard.ps1
```

**Linux/Mac/WSL:**
```bash
# Make executable (first time only)
chmod +x run_dashboard.sh

# Run the dashboard
./run_dashboard.sh
```

#### **Option B: Using Python Launcher**
```bash
python run_dashboard.py
```

#### **Option C: Direct Streamlit**
```bash
streamlit run dashboard_app/research_dashboard.py
```

The dashboard opens at `http://localhost:8501` with:
- **📊 Overview**: Key metrics, recent papers, search functionality  
- **📈 Publication Trends**: Timeline analysis, journal insights, topic distribution
- **👥 Authors & Institutions**: Top researchers, performance metrics, geographic analysis
- **🔬 Research Topics**: AI/ML trends, topic analysis, detailed breakdowns
- **🌍 Geographic Analysis**: Global research distribution and quality metrics

### **Launcher Script Features:**
- ✅ **Automatic Environment Setup**: Creates and activates virtual environment
- ✅ **Dependency Installation**: Installs required packages automatically
- ✅ **Database Connection Test**: Verifies database connectivity
- ✅ **Error Handling**: Clear error messages and troubleshooting tips
- ✅ **Cross-Platform**: Works on Windows, Linux, Mac, and WSL

---

## Data Pipeline Usage

### Option 1: Consolidated Pipeline (Recommended)

Run the complete pipeline with a single command:

```bash
# Run the complete pipeline
python pipeline/pipeline.py

# Dry run (validate without making changes)
python pipeline/pipeline.py --dry-run

# Use custom configuration
python pipeline/pipeline.py --config my_config.yaml

# Enable verbose logging
python pipeline/pipeline.py --verbose
```

**Pipeline Configuration**

The pipeline uses `pipeline/pipeline_config.yaml` for configuration:

```yaml
api:
  days_back: 3 # Days to look back for papers
  min_ai_score: 0.7 # Minimum AI relevance score
  output_dir: "temp" # Temporary files directory

database:
  schema_file: "database/schema.sql"
  deploy_schema: true # Whether to ensure schema exists

testing:
  run_tests: true # Whether to run quality tests
  config_file: "database/test_config.yaml"

logging:
  level: "INFO" # Log level
  log_dir: "logs" # Log files directory
```

**Pipeline Stages**

The pipeline performs these stages in sequence:

1. **Fetch Papers**: Uses `pipeline/fetch_ai_papers.py` to get recent AI papers from OpenAlex API
2. **Deploy Schema**: Ensures database tables exist using `database/deploy_schema.py`
3. **Load Data**: Processes and imports papers using `database/import_papers.py`
4. **Quality Tests**: Runs comprehensive data validation using `database/test_papers_table.py`

**Example Pipeline Output**

```
======================================================================
RESEARCH PAPERS DATA PIPELINE STARTED
======================================================================
Configuration: pipeline_config.yaml
Dry run mode: False

Stage 1: Fetching AI papers from last 3 days...
✅ Successfully fetched 1638 AI papers

Stage 2: Ensuring database schema...
✅ Database schema ensured successfully

Stage 3: Loading papers to database...
✅ Processed 1638 papers (1620 inserted, 18 updated)

Stage 4: Running quality tests...
✅ All 18 tests passed

======================================================================
PIPELINE COMPLETED SUCCESSFULLY
======================================================================
Duration: 45.23 seconds
Papers Fetched: 1638
Papers Processed: 1638
Tests Passed: 18
```

### Option 2: Individual Script Execution

You can also run individual components of the pipeline:

#### Fetch AI Research Papers

Fetch recent AI papers from OpenAlex (last 3 days):

```bash
python pipeline/fetch_ai_papers.py
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

#### Import Papers to Database

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

#### Test Database Connection

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
├── pipeline/                # 🔄 Data Pipeline Components
│   ├── pipeline.py          # Consolidated pipeline orchestrator
│   ├── pipeline_config.yaml # Pipeline configuration
│   └── fetch_ai_papers.py   # OpenAlex API fetcher
├── dashboard_app/           # 📊 Analytics Dashboard Components
│   ├── research_dashboard.py # Streamlit analytics dashboard
│   └── dashboard_config.py  # Dashboard configuration & utilities
├── database/                # 🗄️ Database Management
│   ├── database.py          # Database connection utilities
│   ├── deploy_schema.py     # Schema deployment script
│   ├── import_papers.py     # Paper import ETL script
│   ├── test_papers_table.py # Data quality test runner
│   ├── schema.sql           # Database schema definition
│   ├── test_database.py     # Database connection tests
│   ├── test_config.yaml     # Data quality test configuration
│   ├── tests/               # SQL test files by category
│   └── SCHEMA_SUMMARY.md    # Schema documentation
├── logs/                    # 📄 Import logs (timestamped)
├── temp/                    # 📁 Temporary JSON files
├── run_dashboard.py         # 🐍 Python dashboard launcher
├── run_dashboard.sh         # 🐧 Linux/Mac bash launcher
├── run_dashboard.bat        # 🪟 Windows batch launcher
├── run_dashboard.ps1        # 💎 PowerShell launcher
├── requirements.txt         # Python dependencies
├── env.template             # Environment variable template
└── README.md               # This comprehensive guide
```

## Workflow Options

### Option A: Consolidated Pipeline (Recommended)

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Run complete pipeline
python pipeline/pipeline.py --verbose

# Check logs for details
type logs\pipeline_*.log
```

### Option B: Individual Script Execution

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# 1. Fetch recent papers
python pipeline/fetch_ai_papers.py

# 2. Deploy schema (if needed)
python database/deploy_schema.py

# 3. Import to database (use the generated filename)
python database/import_papers.py temp/ai_papers_2025-11-14_13-04-35.json

# 4. Run data quality tests
python database/test_papers_table.py

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

## Data Quality Testing

The pipeline includes comprehensive data quality validation with 18 tests across 6 categories:

### Test Categories

1. **Data Completeness** (3 tests)

   - Missing titles, publication info, authors

2. **Data Validity** (3 tests)

   - Invalid years, negative counts, date mismatches

3. **Business Logic** (2 tests)

   - Open access inconsistencies, invalid percentiles

4. **Data Quality** (3 tests)

   - Duplicate DOIs, suspicious citations, retracted papers

5. **Referential Integrity** (2 tests)

   - Orphaned records, missing first authors

6. **Timestamps & Metadata** (2 tests)
   - Future dates, invalid timestamps

### Running Quality Tests

```bash
# Run all tests
python database/test_papers_table.py

# Run with verbose output
python database/test_papers_table.py --verbose

# Use custom configuration
python database/test_papers_table.py --config custom_test_config.yaml
```

## Logging

All operations are logged to `logs/` directory with timestamps:

- **Pipeline**: Complete workflow logs (`pipeline_*.log`)
- **Import**: Detailed import operations (`import_papers_*.log`)
- **Tests**: Data quality test results (`test_results.txt`)
- **Console**: INFO level messages (progress, summary)
- **File**: DEBUG level messages (detailed operations, errors)

Log files include:

- Detailed transformation steps
- Database operations (inserts/updates)
- Data quality test results
- Error messages with stack traces
- Final statistics summary

## Troubleshooting

### Dashboard Issues

**Dashboard won't start:**
- Check if all dependencies are installed: `pip install -r requirements.txt`
- Verify virtual environment is activated
- Ensure Streamlit is properly installed
- Use launcher scripts for automatic environment setup

**Database connection errors:**
- Verify `.env` file has correct credentials
- Check database connectivity using `python database/database.py`
- Ensure Neon database is accessible from your network
- Test with: `python database/test_database.py`

**Slow dashboard performance:**
- Database queries are cached for 5 minutes
- Large datasets may take time to load initially
- Consider adjusting cache TTL in `dashboard_app/dashboard_config.py`

**Empty visualizations:**
- Check if database has data (run pipeline first)
- Verify date range filters aren't too restrictive
- Ensure database queries are returning results

**Launcher script issues:**
- **Permission Denied (Linux/Mac)**: `chmod +x run_dashboard.sh`
- **PowerShell Execution Policy (Windows)**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **Python Not Found**: Install Python 3.7+ and add to PATH

### Pipeline Issues

**Database Connection Issues:**
1. Check `.env` file exists and has correct credentials
2. Verify database is accessible from your network
3. Run `python database/test_database.py` for diagnostics

**Import Failures:**
1. Check log files in `logs/` directory for detailed errors
2. Verify JSON file format matches OpenAlex schema
3. Ensure database schema is deployed (`deploy_schema.py`)
4. Run data quality tests to identify specific issues

**Pipeline Failures:**
1. Check pipeline logs (`logs/pipeline_*.log`) for stage-specific errors
2. Use `--dry-run` flag to validate configuration without making changes
3. Run individual stages separately to isolate issues
4. Verify all dependencies are installed (`pip install -r requirements.txt`)

### API Rate Limits

The fetcher includes automatic retry with exponential backoff:

- Max 10 retry attempts
- Initial delay: 1 second
- Exponential backoff multiplier: 2x

## Exit Codes

- **Pipeline**: `0` = Success, `1` = Failure
- **Individual Scripts**: `0` = Success, `1` = Failure

## Error Handling

- Each pipeline stage validates success before proceeding
- Comprehensive error tracking and reporting
- Automatic cleanup of temporary files
- Graceful handling of interruptions
- Detailed logging for debugging

## Dashboard Launcher Scripts

Multiple launcher scripts are provided for easy dashboard execution across different platforms:

| Script | Platform | Features |
|--------|----------|----------|
| `run_dashboard.bat` | Windows CMD | Native batch script, user-friendly prompts |
| `run_dashboard.ps1` | Windows PowerShell | Advanced features, colored output |
| `run_dashboard.sh` | Linux/Mac/WSL | Bash script with error trapping |
| `run_dashboard.py` | All Platforms | Cross-platform Python launcher |

### **Automated Setup Process**
1. ✅ **Environment Check**: Verifies you're in the correct directory
2. ✅ **Virtual Environment**: Creates `.venv` if it doesn't exist
3. ✅ **Dependencies**: Installs packages from `requirements.txt`
4. ✅ **Database Test**: Checks connection to your Neon database
5. ✅ **Streamlit Launch**: Starts the dashboard server

### **Platform-Specific Features**

**Bash Script (`run_dashboard.sh`)**
- 🌈 Colored output with progress indicators
- 🛡️ Error trapping with line numbers
- ⚙️ Smart Python detection (python3/python)

**Batch Script (`run_dashboard.bat`)**
- 🪟 Native Windows compatibility
- 📱 User-friendly prompts and validation
- 📂 Comprehensive file checking

**PowerShell Script (`run_dashboard.ps1`)**
- 💎 Advanced PowerShell functionality
- 🎨 Professional colored output
- 🛠️ Enhanced error handling

**Python Launcher (`run_dashboard.py`)**
- 🐍 Cross-platform compatibility
- 🔌 Deep database integration
- 📊 Detailed validation reporting

### **Quick Launcher Guide**
- **Windows users**: Use `run_dashboard.bat` (easiest)
- **Linux/Mac users**: Use `run_dashboard.sh` (native bash)
- **Developers**: Use `run_dashboard.py` (most detailed)
- **Automation**: Any script works for CI/CD integration

## Contributing

When adding new features:

1. Update the database schema in `database/schema.sql`
2. Redeploy schema using `database/deploy_schema.py`
3. Update transformation logic in `database/import_papers.py`
4. Add data quality tests in `database/tests/`
5. Update pipeline configuration in `pipeline/pipeline_config.yaml` if needed
6. Add dashboard queries in `dashboard_app/dashboard_config.py` if needed
7. Update launcher scripts if new dependencies are required
8. Add tests to verify functionality
9. Update this README with new features
