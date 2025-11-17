-- ============================================================================
-- Timestamp & Metadata Tests
-- ============================================================================
-- Purpose: Verify that timestamps and metadata fields are logically consistent
-- Expected: All counts should be 0 (timestamps should be valid)
-- ============================================================================

-- ============================================================================
-- Test 6.1: Future-Dated Papers
-- ============================================================================
-- Papers with publication dates in the future
-- Expected: 0 (papers can't be published in the future)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Future-dated papers' as test_name
FROM papers
WHERE publication_date > CURRENT_DATE;

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    publication_date, 
    publication_year, 
    created_date,
    (publication_date - CURRENT_DATE) as days_in_future
FROM papers
WHERE publication_date > CURRENT_DATE
ORDER BY publication_date DESC
LIMIT 10;

-- ============================================================================
-- Test 6.2: Invalid Ingestion Timestamps
-- ============================================================================
-- Papers where ingested_at is before created_date
-- Expected: 0 (can't ingest before creation)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Invalid ingestion timestamps' as test_name
FROM papers
WHERE created_date IS NOT NULL 
  AND ingested_at < created_date;

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    created_date, 
    ingested_at,
    (created_date - ingested_at) as time_difference,
    publication_year
FROM papers
WHERE created_date IS NOT NULL 
  AND ingested_at < created_date
ORDER BY (created_date - ingested_at) DESC
LIMIT 10;

-- ============================================================================
-- End of Timestamp & Metadata Tests
-- ============================================================================

