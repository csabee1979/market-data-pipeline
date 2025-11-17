-- ============================================================================
-- Referential Integrity Tests
-- ============================================================================
-- Purpose: Verify foreign key relationships and data consistency across tables
-- Expected: All counts should be 0 (foreign keys should be enforced)
-- ============================================================================

-- ============================================================================
-- Test 5.1: Orphaned Paper-Authors Records
-- ============================================================================
-- paper_authors records pointing to non-existent papers
-- Expected: 0 (foreign key constraint should prevent this)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Orphaned paper_authors records' as test_name
FROM paper_authors pa
LEFT JOIN papers p ON pa.paper_id = p.paper_id
WHERE p.paper_id IS NULL;

-- Sample failing records
SELECT 
    pa.paper_id, 
    pa.author_id, 
    pa.author_position, 
    pa.author_sequence,
    pa.is_corresponding,
    pa.created_at
FROM paper_authors pa
LEFT JOIN papers p ON pa.paper_id = p.paper_id
WHERE p.paper_id IS NULL
ORDER BY pa.created_at DESC
LIMIT 10;

-- ============================================================================
-- Test 5.2: Missing First Authors
-- ============================================================================
-- Papers with first_author_name but no first author in paper_authors
-- Expected: 0 (if first_author_name is set, should have matching record)

-- Count of failures
SELECT 
    COUNT(*) as failure_count,
    'Missing first author in paper_authors' as test_name
FROM papers p
WHERE p.first_author_name IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM paper_authors pa
    WHERE pa.paper_id = p.paper_id 
      AND pa.author_position = 'first'
  );

-- Sample failing records
SELECT 
    p.paper_id, 
    p.doi, 
    p.title, 
    p.first_author_name, 
    p.author_count,
    (SELECT COUNT(*) FROM paper_authors pa WHERE pa.paper_id = p.paper_id) as actual_author_count
FROM papers p
WHERE p.first_author_name IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM paper_authors pa
    WHERE pa.paper_id = p.paper_id 
      AND pa.author_position = 'first'
  )
ORDER BY p.publication_year DESC
LIMIT 10;

-- ============================================================================
-- End of Referential Integrity Tests
-- ============================================================================

