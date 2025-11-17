-- ============================================================================
-- Data Quality & Anomaly Detection Tests
-- ============================================================================
-- Purpose: Identify data quality issues, duplicates, and suspicious patterns
-- Expected: Low counts or 0 for most tests
-- ============================================================================

-- ============================================================================
-- Test 4.1: Duplicate DOIs
-- ============================================================================
-- Multiple papers with the same DOI
-- Expected: 0 (DOIs should be unique identifiers)

-- Count of failures (groups with duplicates)
SELECT 
    COUNT(*) as failure_count,
    'Duplicate DOIs' as test_name
FROM (
    SELECT doi, COUNT(*) as duplicate_count
    FROM papers
    WHERE doi IS NOT NULL
    GROUP BY doi
    HAVING COUNT(*) > 1
) duplicates;

-- Sample failing records
SELECT 
    doi, 
    COUNT(*) as paper_count, 
    STRING_AGG(paper_id, ', ' ORDER BY paper_id) as paper_ids,
    STRING_AGG(title, ' | ' ORDER BY paper_id) as titles
FROM papers
WHERE doi IS NOT NULL
GROUP BY doi
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 10;

-- ============================================================================
-- Test 4.2: Suspicious Citation Counts
-- ============================================================================
-- Papers with unrealistically high citation counts
-- Expected: Low count (threshold configurable, default 100,000)
-- Note: This threshold is parameterized in the Python script

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Suspicious citation counts (>100000)' as test_name
FROM papers
WHERE cited_by_count > 100000;

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    cited_by_count, 
    publication_year, 
    journal_name,
    fwci,
    citation_percentile
FROM papers
WHERE cited_by_count > 100000
ORDER BY cited_by_count DESC
LIMIT 10;

-- ============================================================================
-- Test 4.3: Recently Updated Retracted Papers
-- ============================================================================
-- Retracted papers updated recently (may need review)
-- Expected: Low count (retracted papers shouldn't be frequently updated)
-- Note: Time window is parameterized in the Python script (default 30 days)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Recently updated retracted papers (last 30 days)' as test_name
FROM papers
WHERE is_retracted = TRUE 
  AND updated_date > CURRENT_DATE - INTERVAL '30 days';

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    is_retracted, 
    updated_date, 
    publication_year,
    journal_name,
    cited_by_count
FROM papers
WHERE is_retracted = TRUE 
  AND updated_date > CURRENT_DATE - INTERVAL '30 days'
ORDER BY updated_date DESC
LIMIT 10;

-- ============================================================================
-- End of Data Quality Tests
-- ============================================================================

