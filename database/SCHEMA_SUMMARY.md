# Research Papers Database - Complete Documentation

## 📚 Overview

This database schema is designed for **dashboard analytics** of academic research papers from OpenAlex API. It includes **three tables**: papers, authors, and paper_authors (junction table), focusing on **quantitative metrics** and **essential categorical data** while maintaining proper relational structure.

### What This Database Provides

- ✅ **Papers**: Full publication details, citations, journals, open access status
- ✅ **Authors**: Complete author information with auto-updated metrics
- ✅ **Relationships**: Many-to-many paper-author links with affiliations
- ✅ **Performance**: 39 indexes for fast queries
- ✅ **Automation**: Triggers for automatic metric updates

## Key Design Principles

1. **Normalized Structure**: Three-table design with proper relationships (papers ↔ paper_authors ↔ authors)
2. **Dashboard-Optimized**: Fields selected specifically for visualization and analytics
3. **Performance-Focused**: Comprehensive indexing (40+ indexes) for common query patterns
4. **Quantitative Emphasis**: Rich citation and impact metrics for both papers and authors
5. **Essential Categories Only**: Key filters like journal, OA status, topics, author positions
6. **Automatic Updates**: Author metrics auto-update via database triggers

## Database Structure

### Three-Table Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│   papers    │         │  paper_authors   │         │   authors   │
│             │◄───────►│  (junction)      │◄───────►│             │
│ paper_id PK │         │ paper_id FK      │         │ author_id PK│
│ title       │         │ author_id FK     │         │ display_name│
│ citations   │         │ position         │         │ orcid       │
│ ...         │         │ corresponding    │         │ total_papers│
└─────────────┘         │ institutions[]   │         │ ...         │
                        └──────────────────┘         └─────────────┘
```

## Schema Highlights

### 📄 Papers Table (42 fields)

#### 📊 Quantitative Measures (for charts/graphs)

| Field                    | Description                    | Use Case                         |
| ------------------------ | ------------------------------ | -------------------------------- |
| `cited_by_count`         | Number of citations            | Impact tracking, trending papers |
| `referenced_works_count` | Number of references           | Research depth analysis          |
| `fwci`                   | Field-Weighted Citation Impact | Normalized impact comparison     |
| `citation_percentile`    | Percentile ranking             | Top performers identification    |
| `author_count`           | Number of authors              | Collaboration analysis           |
| `institution_count`      | Number of institutions         | Multi-institutional research     |
| `country_count`          | Number of countries            | International collaboration      |
| `publication_year`       | Year published                 | Temporal trends                  |

#### 🏷️ Essential Categorical Measures (for filtering/grouping)

| Field               | Description                | Dashboard Use                               |
| ------------------- | -------------------------- | ------------------------------------------- |
| `journal_name`      | Journal/venue name         | Top journals, journal comparison            |
| `publisher`         | Publisher name             | Publisher analysis                          |
| `oa_status`         | Open access status         | OA trends (gold/hybrid/green/bronze/closed) |
| `paper_type`        | Type of publication        | Article vs preprint analysis                |
| `is_open_access`    | Boolean OA flag            | Quick OA filtering                          |
| `first_country`     | First author's country     | Geographic distribution                     |
| `first_institution` | First author's institution | Institutional productivity                  |
| `primary_topic`     | Main research topic        | Topic-based filtering                       |
| `top_concept_1/2/3` | Top 3 concepts             | Research area classification                |
| `is_retracted`      | Retraction flag            | Quality control                             |
| `has_ai_field`      | AI/ML relevance            | Domain-specific filtering                   |

#### 🔍 Identifiers & Links

- `paper_id` (Primary Key): OpenAlex ID
- `doi`: Digital Object Identifier
- `title`: Paper title
- `pdf_url`: Direct PDF link
- `landing_page_url`: Main paper page

### 👤 Authors Table (11 fields)

**Author Information:**

- `author_id` (Primary Key): OpenAlex author ID
- `display_name`: Author's name
- `orcid`: ORCID identifier (75% coverage)

**Aggregated Metrics (Auto-Updated):**

- `total_papers`: Count of papers in our DB
- `total_citations`: Sum of citations across all papers
- `h_index`: H-index metric
- `primary_institution`: Most frequent institution
- `primary_country`: Most frequent country
- `first_seen_date`, `last_seen_date`: Date ranges

### 🔗 Paper-Authors Junction Table

**Relationship Data:**

- `paper_id`, `author_id` (Composite Primary Key)
- `author_position`: first/middle/last
- `author_sequence`: 1, 2, 3, ... (order in list)
- `is_corresponding`: Corresponding author flag

**Affiliation Arrays:**

- `institution_names[]`: Array of institutions for this paper
- `institution_ids[]`: OpenAlex institution IDs
- `countries[]`: Country codes
- `raw_affiliation_strings[]`: Raw affiliation text

### 📈 Sample Dashboard Queries

The schema includes examples for:

**Papers:**

- Top cited papers by year
- Open access trends over time
- Top journals by paper count
- High-impact papers (FWCI > 1.5)
- Topic/concept analysis

**Authors:**

- Most prolific authors
- Top cited authors
- Co-author networks
- International collaborations
- First/last/corresponding author analysis

## Key Features

### ✨ Automatic Metric Updates

- Author metrics (total_papers, total_citations, date ranges) **auto-update** via database trigger
- No manual maintenance needed!

### 🔍 Powerful Queries Enabled

- **Papers**: Citations, journals, open access, topics
- **Authors**: Productivity, collaborations, positions
- **Combined**: First-author papers, co-author networks, international collaborations

### 📊 Sample Statistics (from 500 papers)

- **2,351 authorships**
- **1,574 unique authors**
- **75% have ORCID**
- **4.7 avg authors per paper**

## What Was Excluded (Intentionally)

To keep the schema dashboard-focused, we excluded:

❌ **Full abstract text** (kept only boolean flag)  
❌ **Detailed bibliographic info** (volume, issue, pages)  
❌ **Complete reference lists** (kept only count)  
❌ **Funding details** (grants, funders)  
❌ **MeSH terms** (medical subject headings)  
❌ **Sustainable development goals**

✅ **Authors are now fully supported** via separate authors table!

## Files in This Repository

### SQL Schema

- **`schema.sql`** - Complete PostgreSQL schema with:
  - **3 tables**: papers, authors, paper_authors
  - **39 indexes** for optimal performance
  - **Automatic triggers** for author metric updates
  - **Helper views**: first_authors, corresponding_authors, author_productivity
  - Constraints and validations
  - Inline documentation

### Python Utilities

- **`database.py`** - Database connection module for PostgreSQL (Neon)

### Documentation

- **`SCHEMA_SUMMARY.md`** - This file (complete documentation)

## 🚀 Quick Start Guide

### Step 1: Review the Schema

```bash
# Review the SQL file
cat schema.sql

# Or review this documentation
cat SCHEMA_SUMMARY.md
```

### Step 2: Create Database Tables

**Option A: Using psql**

```bash
psql -h your-host -d your-db -U your-user -f schema.sql
```

**Option B: Using Python (with existing database.py)**

```python
from database import execute_query

with open('schema.sql', 'r') as f:
    schema_sql = f.read()
    execute_query(schema_sql, fetch=False)
```

### Step 3: Verify Tables Created

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('papers', 'authors', 'paper_authors');

-- Check indexes
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check views
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public';
```

### Step 4: Load Data (ETL)

Create an ETL script to transform JSON → database:

```python
# Suggested workflow
papers = load_json('temp/ai_papers_*.json')

for paper in papers:
    # 1. Extract paper data
    paper_data = extract_paper_fields(paper)
    insert_paper(paper_data)

    # 2. Extract and insert authors
    for authorship in paper['authorships']:
        author_data = extract_author_fields(authorship)
        upsert_author(author_data)  # Use UPSERT for duplicates

        # 3. Insert paper-author relationship
        insert_paper_author(paper_id, author_id, authorship_details)

    # Author metrics auto-update via trigger!
```

**Key ETL Considerations:**

- Use **UPSERT** (ON CONFLICT UPDATE) for authors
- **Batch inserts** for performance (100-1000 records)
- Handle **NULL values** appropriately
- **Validate data** before insert
- **Log errors** for debugging
- **Commit** every N papers for progress tracking

### Step 5: Build Dashboards

Connect to PostgreSQL and create visualizations using the sample queries below.

## 🔍 Sample Queries

### Papers Queries

```sql
-- Top cited papers this year
SELECT title, journal_name, cited_by_count
FROM papers
WHERE publication_year = 2025
ORDER BY cited_by_count DESC
LIMIT 10;

-- Open access trends over time
SELECT publication_year, oa_status, COUNT(*) as paper_count
FROM papers
GROUP BY publication_year, oa_status
ORDER BY publication_year DESC;

-- Top journals by paper count
SELECT journal_name,
       COUNT(*) as papers,
       AVG(cited_by_count) as avg_citations
FROM papers
GROUP BY journal_name
ORDER BY papers DESC
LIMIT 20;

-- High-impact papers (FWCI > 1.5)
SELECT title, journal_name, fwci, cited_by_count
FROM papers
WHERE fwci >= 1.5
ORDER BY fwci DESC
LIMIT 50;
```

### Authors Queries

```sql
-- Top authors by paper count
SELECT display_name, total_papers, total_citations, primary_institution
FROM authors
ORDER BY total_papers DESC
LIMIT 20;

-- Top authors by citations
SELECT display_name, total_citations, total_papers,
       ROUND(total_citations::NUMERIC / NULLIF(total_papers, 0), 2) as avg_citations
FROM authors
ORDER BY total_citations DESC
LIMIT 20;

-- Find all papers by a specific author
SELECT p.title, p.publication_year, p.journal_name, p.cited_by_count,
       pa.author_position, pa.is_corresponding
FROM paper_authors pa
JOIN papers p ON pa.paper_id = p.paper_id
WHERE pa.author_id = 'https://openalex.org/A...'
ORDER BY p.publication_date DESC;

-- Find co-authors of a specific author
SELECT a2.display_name, COUNT(*) as collaboration_count
FROM paper_authors pa1
JOIN paper_authors pa2 ON pa1.paper_id = pa2.paper_id
JOIN authors a2 ON pa2.author_id = a2.author_id
WHERE pa1.author_id = 'https://openalex.org/A...'
  AND pa2.author_id != pa1.author_id
GROUP BY a2.display_name
ORDER BY collaboration_count DESC
LIMIT 20;
```

### Combined Queries

```sql
-- First-author papers with citations
SELECT p.title, a.display_name as first_author,
       p.journal_name, p.publication_year, p.cited_by_count
FROM papers p
JOIN paper_authors pa ON p.paper_id = pa.paper_id
JOIN authors a ON pa.author_id = a.author_id
WHERE pa.author_position = 'first'
ORDER BY p.cited_by_count DESC
LIMIT 20;

-- Authors with international collaborations
SELECT a.display_name, a.total_papers,
       COUNT(DISTINCT unnest(pa.countries)) as distinct_countries
FROM paper_authors pa
JOIN authors a ON pa.author_id = a.author_id
GROUP BY a.author_id, a.display_name, a.total_papers
HAVING COUNT(DISTINCT unnest(pa.countries)) > 1
ORDER BY distinct_countries DESC
LIMIT 20;

-- Most prolific corresponding authors
SELECT a.display_name,
       COUNT(*) as corresponding_papers,
       a.total_papers
FROM paper_authors pa
JOIN authors a ON pa.author_id = a.author_id
WHERE pa.is_corresponding = TRUE
GROUP BY a.author_id, a.display_name, a.total_papers
ORDER BY corresponding_papers DESC
LIMIT 20;
```

## 🎯 Dashboard Ideas

### Paper Analytics Widgets

- 📈 **Citation trends over time** (line chart)
- 📊 **Papers by journal/publisher** (bar chart)
- 🔓 **Open access adoption rates** (pie chart, trend line)
- 🌍 **Geographic distribution** (world map)
- 📚 **Top cited papers** (table with filters)
- 🏷️ **Topic/concept analysis** (word cloud, treemap)

### Author Analytics Widgets

- 👤 **Most prolific authors** (leaderboard)
- ⭐ **Most cited authors** (leaderboard)
- 🤝 **Collaboration networks** (network graph)
- 🌐 **International collaborations** (map, sankey diagram)
- 🏛️ **Top institutions** (bar chart)
- 📍 **Authors by country** (choropleth map)

### Combined Analytics

- 👥 **First vs last authorship patterns** (stacked bar)
- ✉️ **Corresponding author analysis** (table)
- 🔬 **Research group productivity** (grouped bar)
- 📊 **Institution rankings** (table with metrics)
- 🌟 **Rising stars** (recent high-impact authors)

## Schema Statistics

### Papers Table

- **Total Fields**: 42 columns
- **Quantitative Fields**: 8
- **Categorical Fields**: 15
- **Indexes**: 22 indexes

### Authors Table

- **Total Fields**: 11 columns
- **Auto-Updated Fields**: 4 (via trigger)
- **Indexes**: 8 indexes

### Paper-Authors Junction

- **Total Fields**: 8 columns
- **Array Fields**: 4 (institutions, countries, etc.)
- **Indexes**: 9 indexes (including GIN for arrays)

### Overall

- **Total Tables**: 3
- **Total Indexes**: 39 indexes
- **Total Views**: 3 helper views
- **Triggers**: 1 automatic update trigger

## Performance Considerations

The schema includes indexes for:

**Papers:**

- ✅ Date-based queries (year, publication_date)
- ✅ Citation metrics (sorting by impact)
- ✅ Full-text search on titles
- ✅ Categorical filtering (journal, OA status, country)
- ✅ Composite queries (year + citations, journal + year)

**Authors:**

- ✅ Name search (including fuzzy matching support)
- ✅ ORCID lookups
- ✅ Productivity metrics (papers, citations, h-index)
- ✅ Geographic filtering (institution, country)

**Paper-Authors:**

- ✅ Foreign key lookups (paper_id, author_id)
- ✅ Position queries (first/last/corresponding)
- ✅ Array searches (countries, institutions) via GIN indexes
- ✅ Composite indexes for common patterns

## 🛠️ Maintenance & Operations

### Regular Maintenance Tasks

```sql
-- Update table statistics for query optimization
ANALYZE papers;
ANALYZE authors;
ANALYZE paper_authors;

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Backup & Restore

```bash
# Backup entire database
pg_dump -h host -U user -d database > backup.sql

# Backup specific tables
pg_dump -h host -U user -d database \
  -t papers -t authors -t paper_authors > backup.sql

# Restore
psql -h host -U user -d database < backup.sql
```

### Updating Data from OpenAlex

```python
# Use UPSERT to update existing records with new citation counts
INSERT INTO papers (paper_id, title, cited_by_count, ...)
VALUES (...)
ON CONFLICT (paper_id)
DO UPDATE SET
    cited_by_count = EXCLUDED.cited_by_count,
    updated_date = EXCLUDED.updated_date,
    ingested_at = CURRENT_TIMESTAMP;
```

## ❓ FAQ

**Q: Why three tables instead of one?**  
A: Normalized design prevents data duplication, enables efficient updates, and supports complex author queries.

**Q: Why use arrays for affiliations?**  
A: Authors often have multiple affiliations. Arrays keep it simple while preserving all data. PostgreSQL arrays are efficient and queryable with GIN indexes.

**Q: How are author metrics updated?**  
A: Automatically via database trigger when paper_authors changes. No manual work needed!

**Q: Can I add more fields?**  
A: Yes! Check the OpenAlex API documentation for all available fields: https://docs.openalex.org/

**Q: What about institutions as a separate table?**  
A: Could be added if needed, but arrays are sufficient for dashboard analytics. Consider normalizing if you need complex institution queries.

**Q: How to handle updates from OpenAlex?**  
A: Use UPSERT (ON CONFLICT UPDATE) to update existing records with new citation counts and metrics.

**Q: What if I need full abstracts?**  
A: Add a TEXT column with GIN index for full-text search: `ALTER TABLE papers ADD COLUMN abstract TEXT; CREATE INDEX idx_papers_abstract ON papers USING gin(to_tsvector('english', abstract));`

## 📦 Repository Files

- **`schema.sql`** - Complete database schema (3 tables, 39 indexes, 3 views, 1 trigger)
- **`database.py`** - Database connection module for PostgreSQL (Neon)
- **`SCHEMA_SUMMARY.md`** - This file (complete documentation)

## 🔗 Resources

- **OpenAlex API**: https://docs.openalex.org/
- **PostgreSQL Arrays**: https://www.postgresql.org/docs/current/arrays.html
- **PostgreSQL GIN Indexes**: https://www.postgresql.org/docs/current/gin.html
- **Database Module**: See `database.py` for connection utilities

## 📝 Additional Notes

### Design Decisions

**Why Normalized (3 tables)?**

- ✅ No data duplication (author names stored once)
- ✅ Easy to update author information
- ✅ Automatic metric aggregation
- ✅ Supports complex queries
- ✅ Standard relational design

**Why Arrays for Affiliations?**

- ✅ Keeps schema simple (no 4th table needed)
- ✅ Preserves all affiliation data
- ✅ PostgreSQL arrays are efficient
- ✅ Easy to query with GIN indexes

**Why Automatic Triggers?**

- ✅ Metrics always up-to-date
- ✅ No manual maintenance
- ✅ Prevents inconsistencies
- ✅ Transparent to application

### Next Enhancements (Optional)

- Add full-text search on author names (pg_trgm extension)
- Add author photo URLs (if available from API)
- Track author affiliations over time (temporal table)
- Calculate collaboration scores
- Add author expertise/topics from papers
- Materialize complex views for performance

---

**Created**: 2025-11-14  
**Updated**: 2025-11-14 (Added authors tables)  
**Source Data**: OpenAlex API (1,727 papers in sample file)  
**Database**: PostgreSQL (Neon)  
**Tables**: 3 (papers, authors, paper_authors)  
**Indexes**: 39 total
