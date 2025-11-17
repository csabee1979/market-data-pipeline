-- ============================================================================
-- Business Logic Tests
-- ============================================================================
-- Purpose: Verify that business rules and data relationships are consistent
-- Expected: All counts should be 0 (business logic should be enforced)
-- ============================================================================

-- ============================================================================
-- Test 3.1: Author Count Mismatches
-- ============================================================================
-- Papers where author_count doesn't match actual count in paper_authors
-- Expected: 0 (aggregated count should match junction table)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Author count mismatch' as test_name
FROM papers p
LEFT JOIN (
    SELECT paper_id, COUNT(*) as actual_count
    FROM paper_authors
    GROUP BY paper_id
) pa ON p.paper_id = pa.paper_id
WHERE p.author_count IS NOT NULL 
  AND COALESCE(pa.actual_count, 0) != p.author_count;

-- Sample failing records
SELECT 
    p.paper_id, 
    p.doi, 
    p.title, 
    p.author_count, 
    COALESCE(pa.actual_count, 0) as actual_author_count,
    ABS(p.author_count - COALESCE(pa.actual_count, 0)) as difference
FROM papers p
LEFT JOIN (
    SELECT paper_id, COUNT(*) as actual_count
    FROM paper_authors
    GROUP BY paper_id
) pa ON p.paper_id = pa.paper_id
WHERE p.author_count IS NOT NULL 
  AND COALESCE(pa.actual_count, 0) != p.author_count
ORDER BY ABS(p.author_count - COALESCE(pa.actual_count, 0)) DESC
LIMIT 10;

-- ============================================================================
-- Test 3.2: Open Access Inconsistencies
-- ============================================================================
-- Papers with inconsistent open access flags and status
-- Expected: 0 (is_open_access should align with oa_status)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Open access flag/status inconsistency' as test_name
FROM papers
WHERE (is_open_access = TRUE AND oa_status IN ('closed', 'null'))
   OR (is_open_access = FALSE AND oa_status IN ('gold', 'hybrid', 'green', 'bronze'));

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    is_open_access, 
    oa_status, 
    pdf_url,
    license
FROM papers
WHERE (is_open_access = TRUE AND oa_status IN ('closed', 'null'))
   OR (is_open_access = FALSE AND oa_status IN ('gold', 'hybrid', 'green', 'bronze'))
ORDER BY publication_year DESC
LIMIT 10;

-- ============================================================================
-- Test 3.3: Invalid Citation Percentiles
-- ============================================================================
-- Papers with citation_percentile outside valid range (0-100)
-- Expected: 0 (percentiles must be between 0 and 100)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Invalid citation percentile' as test_name
FROM papers
WHERE citation_percentile IS NOT NULL 
  AND (citation_percentile < 0 OR citation_percentile > 100);

-- Sample failing records
SELECT 
    paper_id, 
    doi, 
    title, 
    citation_percentile, 
    cited_by_count,
    publication_year
FROM papers
WHERE citation_percentile IS NOT NULL 
  AND (citation_percentile < 0 OR citation_percentile > 100)
ORDER BY citation_percentile DESC
LIMIT 10;

-- ============================================================================
-- End of Business Logic Tests
-- ============================================================================

