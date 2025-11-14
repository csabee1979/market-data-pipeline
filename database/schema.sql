-- ============================================================================
-- Complete Research Papers Database Schema
-- ============================================================================
-- Purpose: Store academic papers and authors for dashboard analytics
-- Tables: papers, authors, paper_authors (junction table)
-- Source: OpenAlex API data
-- ============================================================================

-- ============================================================================
-- PART 1: PAPERS TABLE
-- ============================================================================

DROP TABLE IF EXISTS papers CASCADE;

CREATE TABLE papers (
    -- ========================================================================
    -- Primary Identifiers
    -- ========================================================================
    paper_id VARCHAR(255) PRIMARY KEY,
    doi VARCHAR(255),
    title TEXT NOT NULL,
    
    -- ========================================================================
    -- Publication Information
    -- ========================================================================
    publication_year INTEGER,
    publication_date DATE,
    paper_type VARCHAR(50),
    language VARCHAR(10),
    
    -- ========================================================================
    -- Journal/Source Information
    -- ========================================================================
    journal_name VARCHAR(500),
    publisher VARCHAR(500),
    journal_issn VARCHAR(20),
    is_core_journal BOOLEAN,
    
    -- ========================================================================
    -- Open Access Information
    -- ========================================================================
    is_open_access BOOLEAN,
    oa_status VARCHAR(50),
    pdf_url TEXT,
    landing_page_url TEXT,
    license VARCHAR(100),
    
    -- ========================================================================
    -- Author & Institution Metrics (Aggregated)
    -- ========================================================================
    author_count INTEGER,
    first_author_name VARCHAR(255),
    corresponding_author_name VARCHAR(255),
    institution_count INTEGER,
    country_count INTEGER,
    first_institution VARCHAR(500),
    first_country VARCHAR(5),
    
    -- ========================================================================
    -- Citation & Impact Metrics (Quantitative)
    -- ========================================================================
    cited_by_count INTEGER DEFAULT 0,
    referenced_works_count INTEGER DEFAULT 0,
    fwci NUMERIC(10, 4),
    citation_percentile NUMERIC(5, 2),
    
    -- ========================================================================
    -- Research Topics & Keywords
    -- ========================================================================
    primary_topic VARCHAR(500),
    top_concept_1 VARCHAR(255),
    top_concept_2 VARCHAR(255),
    top_concept_3 VARCHAR(255),
    keywords TEXT[],
    
    -- ========================================================================
    -- Quality & Status Flags
    -- ========================================================================
    is_retracted BOOLEAN DEFAULT FALSE,
    is_paratext BOOLEAN DEFAULT FALSE,
    has_abstract BOOLEAN DEFAULT FALSE,
    
    -- ========================================================================
    -- AI/ML Relevance
    -- ========================================================================
    ai_relevance_score NUMERIC(5, 4),
    has_ai_field BOOLEAN,
    
    -- ========================================================================
    -- Metadata & Timestamps
    -- ========================================================================
    created_date TIMESTAMP,
    updated_date TIMESTAMP,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- ========================================================================
    -- Constraints
    -- ========================================================================
    CONSTRAINT valid_year CHECK (publication_year >= 1900 AND publication_year <= 2100),
    CONSTRAINT valid_citation_count CHECK (cited_by_count >= 0),
    CONSTRAINT valid_reference_count CHECK (referenced_works_count >= 0)
);

-- ============================================================================
-- PART 2: AUTHORS TABLE
-- ============================================================================

DROP TABLE IF EXISTS authors CASCADE;

CREATE TABLE authors (
    -- ========================================================================
    -- Primary Identifier
    -- ========================================================================
    author_id VARCHAR(255) PRIMARY KEY,
    
    -- ========================================================================
    -- Author Information
    -- ========================================================================
    display_name VARCHAR(500) NOT NULL,
    orcid VARCHAR(255),
    
    -- ========================================================================
    -- Aggregated Metrics
    -- ========================================================================
    total_papers INTEGER DEFAULT 0,
    total_citations INTEGER DEFAULT 0,
    h_index INTEGER,
    
    -- ========================================================================
    -- Most Common Affiliations
    -- ========================================================================
    primary_institution VARCHAR(500),
    primary_country VARCHAR(5),
    
    -- ========================================================================
    -- Metadata
    -- ========================================================================
    first_seen_date DATE,
    last_seen_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- ========================================================================
    -- Constraints
    -- ========================================================================
    CONSTRAINT valid_total_papers CHECK (total_papers >= 0),
    CONSTRAINT valid_total_citations CHECK (total_citations >= 0)
);

-- ============================================================================
-- PART 3: PAPER-AUTHORS JUNCTION TABLE
-- ============================================================================

DROP TABLE IF EXISTS paper_authors CASCADE;

CREATE TABLE paper_authors (
    -- ========================================================================
    -- Composite Primary Key
    -- ========================================================================
    paper_id VARCHAR(255) NOT NULL,
    author_id VARCHAR(255) NOT NULL,
    
    -- ========================================================================
    -- Authorship Details
    -- ========================================================================
    author_position VARCHAR(20),
    author_sequence INTEGER,
    is_corresponding BOOLEAN DEFAULT FALSE,
    
    -- ========================================================================
    -- Affiliation Information
    -- ========================================================================
    institution_names TEXT[],
    institution_ids TEXT[],
    countries TEXT[],
    raw_affiliation_strings TEXT[],
    
    -- ========================================================================
    -- Metadata
    -- ========================================================================
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- ========================================================================
    -- Constraints and Keys
    -- ========================================================================
    PRIMARY KEY (paper_id, author_id),
    FOREIGN KEY (paper_id) REFERENCES papers(paper_id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE,
    
    CONSTRAINT valid_sequence CHECK (author_sequence > 0)
);

-- ============================================================================
-- INDEXES FOR PAPERS TABLE
-- ============================================================================

CREATE INDEX idx_papers_doi ON papers(doi);
CREATE INDEX idx_papers_title ON papers USING gin(to_tsvector('english', title));
CREATE INDEX idx_papers_publication_year ON papers(publication_year DESC);
CREATE INDEX idx_papers_publication_date ON papers(publication_date DESC);
CREATE INDEX idx_papers_ingested_at ON papers(ingested_at DESC);
CREATE INDEX idx_papers_cited_by_count ON papers(cited_by_count DESC);
CREATE INDEX idx_papers_fwci ON papers(fwci DESC NULLS LAST);
CREATE INDEX idx_papers_citation_percentile ON papers(citation_percentile DESC NULLS LAST);
CREATE INDEX idx_papers_journal_name ON papers(journal_name);
CREATE INDEX idx_papers_publisher ON papers(publisher);
CREATE INDEX idx_papers_oa_status ON papers(oa_status);
CREATE INDEX idx_papers_paper_type ON papers(paper_type);
CREATE INDEX idx_papers_is_open_access ON papers(is_open_access);
CREATE INDEX idx_papers_first_country ON papers(first_country);
CREATE INDEX idx_papers_first_institution ON papers(first_institution);
CREATE INDEX idx_papers_primary_topic ON papers(primary_topic);
CREATE INDEX idx_papers_top_concept_1 ON papers(top_concept_1);
CREATE INDEX idx_papers_ai_relevance ON papers(ai_relevance_score DESC NULLS LAST);
CREATE INDEX idx_papers_has_ai_field ON papers(has_ai_field);
CREATE INDEX idx_papers_is_retracted ON papers(is_retracted);
CREATE INDEX idx_papers_year_citations ON papers(publication_year DESC, cited_by_count DESC);
CREATE INDEX idx_papers_oa_year ON papers(is_open_access, publication_year DESC);
CREATE INDEX idx_papers_journal_year ON papers(journal_name, publication_year DESC);

-- ============================================================================
-- INDEXES FOR AUTHORS TABLE
-- ============================================================================

CREATE INDEX idx_authors_display_name ON authors(display_name);
CREATE INDEX idx_authors_orcid ON authors(orcid) WHERE orcid IS NOT NULL;
CREATE INDEX idx_authors_total_papers ON authors(total_papers DESC);
CREATE INDEX idx_authors_total_citations ON authors(total_citations DESC);
CREATE INDEX idx_authors_h_index ON authors(h_index DESC NULLS LAST);
CREATE INDEX idx_authors_primary_institution ON authors(primary_institution);
CREATE INDEX idx_authors_primary_country ON authors(primary_country);
CREATE INDEX idx_authors_last_seen ON authors(last_seen_date DESC);

-- ============================================================================
-- INDEXES FOR PAPER-AUTHORS JUNCTION TABLE
-- ============================================================================

CREATE INDEX idx_paper_authors_paper_id ON paper_authors(paper_id);
CREATE INDEX idx_paper_authors_author_id ON paper_authors(author_id);
CREATE INDEX idx_paper_authors_position ON paper_authors(author_position);
CREATE INDEX idx_paper_authors_sequence ON paper_authors(author_sequence);
CREATE INDEX idx_paper_authors_corresponding ON paper_authors(is_corresponding) WHERE is_corresponding = TRUE;
CREATE INDEX idx_paper_authors_author_sequence ON paper_authors(author_id, author_sequence);
CREATE INDEX idx_paper_authors_paper_position ON paper_authors(paper_id, author_position);
CREATE INDEX idx_paper_authors_countries ON paper_authors USING gin(countries);
CREATE INDEX idx_paper_authors_institutions ON paper_authors USING gin(institution_ids);

-- ============================================================================
-- TRIGGER FUNCTION TO UPDATE AUTHOR METRICS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_author_metrics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE authors
    SET 
        total_papers = (
            SELECT COUNT(DISTINCT pa.paper_id)
            FROM paper_authors pa
            WHERE pa.author_id = NEW.author_id
        ),
        first_seen_date = (
            SELECT MIN(p.publication_date)
            FROM paper_authors pa
            JOIN papers p ON pa.paper_id = p.paper_id
            WHERE pa.author_id = NEW.author_id
        ),
        last_seen_date = (
            SELECT MAX(p.publication_date)
            FROM paper_authors pa
            JOIN papers p ON pa.paper_id = p.paper_id
            WHERE pa.author_id = NEW.author_id
        ),
        total_citations = (
            SELECT COALESCE(SUM(p.cited_by_count), 0)
            FROM paper_authors pa
            JOIN papers p ON pa.paper_id = p.paper_id
            WHERE pa.author_id = NEW.author_id
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE author_id = NEW.author_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_author_metrics
AFTER INSERT OR UPDATE ON paper_authors
FOR EACH ROW
EXECUTE FUNCTION update_author_metrics();

-- ============================================================================
-- HELPER VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW first_authors AS
SELECT 
    pa.paper_id,
    pa.author_id,
    a.display_name,
    a.orcid,
    pa.institution_names,
    pa.countries
FROM paper_authors pa
JOIN authors a ON pa.author_id = a.author_id
WHERE pa.author_position = 'first';

CREATE OR REPLACE VIEW corresponding_authors AS
SELECT 
    pa.paper_id,
    pa.author_id,
    a.display_name,
    a.orcid,
    pa.institution_names,
    pa.countries
FROM paper_authors pa
JOIN authors a ON pa.author_id = a.author_id
WHERE pa.is_corresponding = TRUE;

CREATE OR REPLACE VIEW author_productivity AS
SELECT 
    a.author_id,
    a.display_name,
    a.orcid,
    a.total_papers,
    a.total_citations,
    a.h_index,
    ROUND(a.total_citations::NUMERIC / NULLIF(a.total_papers, 0), 2) as avg_citations_per_paper,
    a.primary_institution,
    a.primary_country,
    a.first_seen_date,
    a.last_seen_date,
    EXTRACT(YEAR FROM a.last_seen_date) - EXTRACT(YEAR FROM a.first_seen_date) + 1 as years_active
FROM authors a
WHERE a.total_papers > 0
ORDER BY a.total_citations DESC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE papers IS 'Academic research papers with metrics for dashboard analytics';
COMMENT ON TABLE authors IS 'Unique authors with aggregated metrics across all their papers';
COMMENT ON TABLE paper_authors IS 'Junction table linking papers to authors with authorship details';

-- ============================================================================
-- End of Complete Schema
-- ============================================================================

