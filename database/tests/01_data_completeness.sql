-- ============================================================================
-- Data Completeness Tests
-- ============================================================================
-- Purpose: Verify that required fields are populated in the papers table
-- Expected: All counts should be 0 or very low
-- ============================================================================

-- ============================================================================
-- Test 1.1: Missing Titles
-- ============================================================================
-- Papers with missing or empty titles
-- Expected: 0 (title has NOT NULL constraint)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Missing or empty titles' as test_name
FROM papers
WHERE title IS NULL OR TRIM(title) = '';

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    publication_year,
    created_date
FROM papers
WHERE title IS NULL OR TRIM(title) = ''
LIMIT 10;

-- ============================================================================
-- Test 1.2: Missing Publication Information
-- ============================================================================
-- Papers missing both publication_year and publication_date
-- Expected: Low count (most papers should have at least one)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Missing publication year and date' as test_name
FROM papers
WHERE publication_year IS NULL AND publication_date IS NULL;

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    publication_year, 
    publication_date,
    journal_name,
    created_date
FROM papers
WHERE publication_year IS NULL AND publication_date IS NULL
ORDER BY created_date DESC
LIMIT 10;

-- ============================================================================
-- Test 1.3: Papers Without Authors
-- ============================================================================
-- Papers with no associated authors (orphaned papers)
-- Expected: 0 (every paper should have at least one author)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Papers without authors' as test_name
FROM papers p
LEFT JOIN paper_authors pa ON p.paper_id = pa.paper_id
WHERE pa.paper_id IS NULL;

-- Sample failing records
SELECT 
    p.paper_id, 
    p.doi, 
    p.title, 
    p.publication_year, 
    p.author_count,
    p.first_author_name
FROM papers p
LEFT JOIN paper_authors pa ON p.paper_id = pa.paper_id
WHERE pa.paper_id IS NULL
ORDER BY p.created_date DESC
LIMIT 10;

-- ============================================================================
-- End of Data Completeness Tests
-- ============================================================================

