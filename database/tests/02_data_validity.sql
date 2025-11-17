-- ============================================================================
-- Data Validity Tests
-- ============================================================================
-- Purpose: Verify that data values are within valid ranges and formats
-- Expected: All counts should be 0 (constraints should prevent invalid data)
-- ============================================================================

-- ============================================================================
-- Test 2.1: Invalid Publication Years
-- ============================================================================
-- Papers with publication years outside valid range (1900-2100)
-- Expected: 0 (CHECK constraint should prevent this)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Invalid publication years' as test_name
FROM papers
WHERE publication_year IS NOT NULL 
  AND (publication_year < 1900 OR publication_year > 2100);

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    publication_year, 
    publication_date,
    created_date
FROM papers
WHERE publication_year IS NOT NULL 
  AND (publication_year < 1900 OR publication_year > 2100)
ORDER BY publication_year
LIMIT 10;

-- ============================================================================
-- Test 2.2: Negative Citation Counts
-- ============================================================================
-- Papers with negative citation or reference counts
-- Expected: 0 (CHECK constraints should prevent this)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Negative citation or reference counts' as test_name
FROM papers
WHERE cited_by_count < 0 OR referenced_works_count < 0;

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    cited_by_count, 
    referenced_works_count,
    publication_year
FROM papers
WHERE cited_by_count < 0 OR referenced_works_count < 0
ORDER BY cited_by_count, referenced_works_count
LIMIT 10;

-- ============================================================================
-- Test 2.3: Date/Year Mismatches
-- ============================================================================
-- Papers where publication_date year doesn't match publication_year
-- Expected: 0 (data should be consistent)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Publication date/year mismatch' as test_name
FROM papers
WHERE publication_year IS NOT NULL 
  AND publication_date IS NOT NULL
  AND EXTRACT(YEAR FROM publication_date) != publication_year;

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    publication_year, 
    publication_date,
    EXTRACT(YEAR FROM publication_date) as date_year,
    (publication_year - EXTRACT(YEAR FROM publication_date)) as year_difference
FROM papers
WHERE publication_year IS NOT NULL 
  AND publication_date IS NOT NULL
  AND EXTRACT(YEAR FROM publication_date) != publication_year
ORDER BY ABS(publication_year - EXTRACT(YEAR FROM publication_date)) DESC
LIMIT 10;

-- ============================================================================
-- End of Data Validity Tests
-- ============================================================================

