# Data Quality Tests for Papers Table

This directory contains comprehensive SQL data quality tests for the papers table, designed to identify data integrity issues, constraint violations, and business logic inconsistencies.

## Overview

The test suite includes **18 tests** across **6 categories**:

- **Data Completeness** (3 tests): Missing required fields
- **Data Validity** (3 tests): Invalid data ranges and formats  
- **Business Logic** (3 tests): Business rule violations
- **Data Quality** (3 tests): Duplicates and anomalies
- **Referential Integrity** (2 tests): Foreign key consistency
- **Timestamps & Metadata** (2 tests): Date/time validity

## Quick Start

1. **Activate virtual environment:**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install pyyaml psycopg2-binary python-dotenv
   ```

3. **Run all tests:**
   ```bash
   cd database
   python test_papers_table.py
   ```

## Files Structure

```
database/
├── tests/                          # SQL test files
│   ├── 01_data_completeness.sql    # Missing required fields
│   ├── 02_data_validity.sql        # Invalid data ranges
│   ├── 03_business_logic.sql       # Business rule violations
│   ├── 04_data_quality.sql         # Duplicates and anomalies
│   ├── 05_referential_integrity.sql # Foreign key consistency
│   └── 06_timestamps_metadata.sql  # Date/time validity
├── test_config.yaml                # Configuration file
├── test_papers_table.py            # Main test runner
└── README_TESTS.md                 # This file
```

## Configuration

Edit `test_config.yaml` to customize test behavior:

```yaml
# Key thresholds
suspicious_citation_threshold: 100000    # Citation count threshold
retracted_update_window_days: 30         # Recent update window
max_sample_records: 10                   # Sample records to show

# Output settings
output:
  format: "detailed"                     # detailed, summary, json
  save_to_file: true                     # Save results to file
  output_file: "test_results.txt"        # Output filename
```

## Usage Examples

### Basic Usage
```bash
# Run all tests with default config
python test_papers_table.py

# Use custom config file
python test_papers_table.py --config my_config.yaml

# Save results to specific file
python test_papers_table.py --output my_results.txt

# Verbose output
python test_papers_table.py --verbose
```

### Exit Codes
- `0`: All tests passed
- `1`: One or more tests failed or error occurred

## Test Categories Detail

### 1. Data Completeness Tests (`01_data_completeness.sql`)

**Purpose:** Verify required fields are populated

| Test | Description | Expected Result |
|------|-------------|-----------------|
| 1.1 | Missing or empty titles | 0 (NOT NULL constraint) |
| 1.2 | Missing publication year AND date | Low count |
| 1.3 | Papers without authors | 0 (every paper needs authors) |

### 2. Data Validity Tests (`02_data_validity.sql`)

**Purpose:** Verify data values are within valid ranges

| Test | Description | Expected Result |
|------|-------------|-----------------|
| 2.1 | Invalid publication years (< 1900 or > 2100) | 0 (CHECK constraint) |
| 2.2 | Negative citation/reference counts | 0 (CHECK constraint) |
| 2.3 | Publication date/year mismatches | 0 (should be consistent) |

### 3. Business Logic Tests (`03_business_logic.sql`)

**Purpose:** Verify business rules are enforced

| Test | Description | Expected Result |
|------|-------------|-----------------|
| 3.1 | Author count vs actual authors mismatch | 0 (aggregated data consistency) |
| 3.2 | Open access flag/status inconsistencies | 0 (boolean should match status) |
| 3.3 | Citation percentiles outside 0-100 range | 0 (percentiles must be valid) |

### 4. Data Quality Tests (`04_data_quality.sql`)

**Purpose:** Identify duplicates and suspicious patterns

| Test | Description | Expected Result |
|------|-------------|-----------------|
| 4.1 | Duplicate DOIs | 0 (DOIs should be unique) |
| 4.2 | Suspicious citation counts | Low count (configurable threshold) |
| 4.3 | Recently updated retracted papers | Low count (may need review) |

### 5. Referential Integrity Tests (`05_referential_integrity.sql`)

**Purpose:** Verify foreign key relationships

| Test | Description | Expected Result |
|------|-------------|-----------------|
| 5.1 | Orphaned paper_authors records | 0 (FK constraint should prevent) |
| 5.2 | Missing first authors in paper_authors | 0 (if name set, record should exist) |

### 6. Timestamps & Metadata Tests (`06_timestamps_metadata.sql`)

**Purpose:** Verify timestamp consistency

| Test | Description | Expected Result |
|------|-------------|-----------------|
| 6.1 | Future-dated papers | 0 (can't publish in future) |
| 6.2 | Invalid ingestion timestamps | 0 (can't ingest before creation) |

## Sample Output

```
================================================================================
DATA QUALITY TEST REPORT - PAPERS TABLE
================================================================================
Execution Time: 2024-11-17 11:47:23
Duration: 2.34 seconds
Total Tests: 18
Passed: 16
Failed: 2
Total Data Quality Issues: 127

DATA COMPLETENESS (3/3 passed, 0 issues)
------------------------------------------------------------
[PASS] Missing or empty titles
  Description: Papers with missing or empty titles
  Issues Found: 0
  Execution Time: 0.045s

[PASS] Missing publication year and date
  Description: Papers missing both publication_year and publication_date
  Issues Found: 0
  Execution Time: 0.032s

[PASS] Papers without authors
  Description: Papers with no associated authors
  Issues Found: 0
  Execution Time: 0.078s

DATA QUALITY (2/3 passed, 127 issues)
------------------------------------------------------------
[FAIL] Duplicate DOIs
  Description: Multiple papers with the same DOI
  Issues Found: 5
  Execution Time: 0.156s
  Sample Failing Records:
    1. doi: 10.1234/example, paper_count: 2, paper_ids: W123, W456
    2. doi: 10.5678/sample, paper_count: 3, paper_ids: W789, W012, W345

[FAIL] Suspicious citation counts
  Description: Papers with unrealistically high citation counts
  Issues Found: 122
  Execution Time: 0.089s
  Sample Failing Records:
    1. paper_id: W2741809807, cited_by_count: 156789, title: Highly Cited Paper
    2. paper_id: W2108318292, cited_by_count: 134567, title: Another Popular Paper

================================================================================
SUMMARY
================================================================================
Overall Status: FAIL
Tests Passed: 16/18 (88.9%)
Data Quality Issues: 127

RECOMMENDATIONS:
- Review failing tests and investigate root causes
- Check data import processes for validation gaps
- Consider adding constraints or triggers to prevent issues
- Update data cleaning procedures as needed
```

## Running Individual Test Categories

You can run individual SQL files directly using `psql` or any PostgreSQL client:

```bash
# Run only data completeness tests
psql -h your_host -d your_db -f tests/01_data_completeness.sql

# Run specific test category
psql -h your_host -d your_db -f tests/04_data_quality.sql
```

## Customizing Tests

### Adding New Tests

1. Add SQL queries to appropriate test file in `tests/` directory
2. Follow the existing format:
   ```sql
   -- Test X.Y: Test Name
   -- Description of what this test checks
   -- Expected: What the expected result should be
   
   -- Count of failures
   SELECT COUNT(*) as failure_count, 'Test description' as test_name
   FROM papers WHERE condition;
   
   -- Sample failing records
   SELECT relevant_columns FROM papers 
   WHERE condition LIMIT 10;
   ```

### Modifying Thresholds

Edit `test_config.yaml`:

```yaml
# Increase citation threshold for less strict checking
suspicious_citation_threshold: 500000

# Extend time window for retracted paper updates
retracted_update_window_days: 90

# Show more sample records
max_sample_records: 20
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify `.env` file has correct database credentials
   - Check database is running and accessible
   - Ensure virtual environment is activated

2. **Permission Errors**
   - Verify database user has SELECT permissions on all tables
   - Check if user can access `papers`, `authors`, and `paper_authors` tables

3. **Missing Dependencies**
   ```bash
   pip install pyyaml psycopg2-binary python-dotenv
   ```

4. **Config File Not Found**
   - Ensure `test_config.yaml` exists in the database directory
   - Use `--config` flag to specify different config file

### Debug Mode

Run with verbose logging to see detailed execution:

```bash
python test_papers_table.py --verbose
```

## Integration with CI/CD

Add to your CI pipeline:

```bash
# In your CI script
cd database
python test_papers_table.py --config ci_config.yaml --output ci_results.txt

# Check exit code
if [ $? -eq 0 ]; then
    echo "All data quality tests passed"
else
    echo "Data quality issues detected"
    cat ci_results.txt
    exit 1
fi
```

## Performance Notes

- Tests typically complete in 2-5 seconds for databases with < 1M papers
- For larger databases, consider:
  - Running tests during off-peak hours
  - Using read replicas for test execution
  - Adjusting `max_sample_records` to reduce output size

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the SQL files for test logic
3. Examine the configuration file for customization options
4. Check database logs for connection or permission issues
