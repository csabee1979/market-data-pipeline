"""
Import research papers from JSON files into the database.

This script:
- Loads paper data from OpenAlex JSON format
- Transforms data to match database schema
- Inserts/updates data in papers, authors, and paper_authors tables
- Uses UPSERT strategy for deduplication
- Provides comprehensive logging of operations
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import psycopg2
from psycopg2 import Error as PostgresError
from psycopg2.extras import execute_values

# Import database module from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection, DatabaseConfig


class ImportStats:
    """Track import statistics."""

    def __init__(self):
        self.papers_inserted = 0
        self.papers_updated = 0
        self.papers_failed = 0
        self.authors_inserted = 0
        self.authors_updated = 0
        self.authors_failed = 0
        self.paper_authors_inserted = 0
        self.paper_authors_updated = 0
        self.paper_authors_failed = 0
        self.total_papers_processed = 0
        self.start_time = datetime.now()

    def get_summary(self) -> str:
        """Generate summary statistics string."""
        duration = (datetime.now() - self.start_time).total_seconds()
        return f"""
{'='*70}
IMPORT SUMMARY
{'='*70}
Papers:
  - Processed: {self.total_papers_processed}
  - Inserted:  {self.papers_inserted}
  - Updated:   {self.papers_updated}
  - Failed:    {self.papers_failed}

Authors:
  - Inserted:  {self.authors_inserted}
  - Updated:   {self.authors_updated}
  - Failed:    {self.authors_failed}

Paper-Authors Relationships:
  - Inserted:  {self.paper_authors_inserted}
  - Updated:   {self.paper_authors_updated}
  - Failed:    {self.paper_authors_failed}

Duration: {duration:.2f} seconds
{'='*70}
"""


def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        log_dir: Directory for log files

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    Path(log_dir).mkdir(exist_ok=True)

    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"import_papers_{timestamp}.log")

    # Configure logging
    logger = logging.getLogger("import_papers")
    logger.setLevel(logging.DEBUG)

    # File handler - detailed logs
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler - important messages only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging to: {log_file}")
    return logger


def extract_id_from_url(url: Optional[str]) -> Optional[str]:
    """
    Extract ID from OpenAlex URL.

    Args:
        url: OpenAlex URL (e.g., "https://openalex.org/W7104782608")

    Returns:
        ID without prefix (e.g., "W7104782608") or None
    """
    if not url:
        return None
    return url.split("/")[-1] if "/" in url else url


def safe_get(data: Dict, *keys, default=None) -> Any:
    """
    Safely get nested dictionary values.

    Args:
        data: Dictionary to search
        *keys: Sequence of keys to traverse
        default: Default value if key not found

    Returns:
        Value at nested key or default
    """
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    return result if result is not None else default


def transform_paper_data(paper: Dict, logger: logging.Logger) -> Optional[Dict]:
    """
    Transform JSON paper data to database schema format.

    Args:
        paper: Raw paper data from JSON
        logger: Logger instance

    Returns:
        Transformed paper data dictionary or None if invalid
    """
    try:
        paper_id = extract_id_from_url(paper.get("id"))
        if not paper_id:
            logger.error(f"Paper missing ID: {paper.get('title', 'Unknown')}")
            return None

        # Extract DOI (remove https://doi.org/ prefix if present)
        doi = paper.get("doi", "")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")

        # Primary location data
        primary_loc = paper.get("primary_location") or {}
        source = primary_loc.get("source") or {}

        # Open access data
        oa_data = paper.get("open_access") or {}

        # Topics and concepts
        topics = paper.get("topics") or []
        concepts = paper.get("concepts") or []
        keywords = paper.get("keywords") or []

        # Extract top concepts
        top_concepts = sorted(concepts, key=lambda x: x.get("score", 0), reverse=True)[
            :3
        ]

        # Authorships data for aggregated fields
        authorships = paper.get("authorships") or []

        # Get first author
        first_author = next(
            (a for a in authorships if a.get("author_position") == "first"), None
        )
        first_author_name = (
            safe_get(first_author, "author", "display_name") if first_author else None
        )

        # Get corresponding author
        corresponding_author = next(
            (a for a in authorships if a.get("is_corresponding")), None
        )
        corresponding_author_name = (
            safe_get(corresponding_author, "author", "display_name")
            if corresponding_author
            else None
        )

        # Count unique institutions and countries
        all_institutions = set()
        all_countries = set()
        first_institution = None
        first_country = None

        for authorship in authorships:
            institutions = authorship.get("institutions") or []
            countries = authorship.get("countries") or []

            for inst in institutions:
                inst_name = inst.get("display_name")
                if inst_name:
                    all_institutions.add(inst_name)
                    if not first_institution:
                        first_institution = inst_name

            for country in countries:
                if country:
                    all_countries.add(country)
                    if not first_country:
                        first_country = country

        # Check if paper has abstract
        has_abstract = bool(paper.get("abstract_inverted_index"))

        # AI relevance (placeholder - would need custom logic)
        # For now, check if AI-related concepts are present
        ai_keywords = {
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "neural network",
            "ai",
            "ml",
            "dl",
        }
        title_lower = (paper.get("title") or "").lower()
        concepts_lower = [c.get("display_name", "").lower() for c in concepts]
        keywords_lower = [
            k.get("display_name", "").lower() if isinstance(k, dict) else str(k).lower()
            for k in keywords
        ]

        has_ai_field = any(
            ai_kw in title_lower
            or any(ai_kw in concept for concept in concepts_lower)
            or any(ai_kw in keyword for keyword in keywords_lower)
            for ai_kw in ai_keywords
        )

        ai_relevance_score = 0.5 if has_ai_field else 0.0

        # Build paper data dictionary
        paper_data = {
            "paper_id": paper_id,
            "doi": doi or None,
            "title": paper.get("title") or paper.get("display_name"),
            "publication_year": paper.get("publication_year"),
            "publication_date": paper.get("publication_date"),
            "paper_type": paper.get("type"),
            "language": paper.get("language"),
            "journal_name": source.get("display_name"),
            "publisher": source.get("host_organization_name"),
            "journal_issn": source.get("issn_l"),
            "is_core_journal": source.get("is_core"),
            "is_open_access": oa_data.get("is_oa"),
            "oa_status": oa_data.get("oa_status"),
            "pdf_url": primary_loc.get("pdf_url") or oa_data.get("oa_url"),
            "landing_page_url": primary_loc.get("landing_page_url"),
            "license": primary_loc.get("license"),
            "author_count": len(authorships),
            "first_author_name": first_author_name,
            "corresponding_author_name": corresponding_author_name,
            "institution_count": len(all_institutions),
            "country_count": len(all_countries),
            "first_institution": first_institution,
            "first_country": first_country,
            "cited_by_count": paper.get("cited_by_count", 0),
            "referenced_works_count": paper.get("referenced_works_count", 0),
            "fwci": None,  # Not in OpenAlex basic data
            "citation_percentile": None,  # Not in OpenAlex basic data
            "primary_topic": topics[0].get("display_name") if topics else None,
            "top_concept_1": (
                top_concepts[0].get("display_name") if len(top_concepts) > 0 else None
            ),
            "top_concept_2": (
                top_concepts[1].get("display_name") if len(top_concepts) > 1 else None
            ),
            "top_concept_3": (
                top_concepts[2].get("display_name") if len(top_concepts) > 2 else None
            ),
            "keywords": (
                [
                    k.get("display_name") if isinstance(k, dict) else str(k)
                    for k in keywords
                ]
                if keywords
                else None
            ),
            "is_retracted": paper.get("is_retracted", False),
            "is_paratext": paper.get("is_paratext", False),
            "has_abstract": has_abstract,
            "ai_relevance_score": ai_relevance_score,
            "has_ai_field": has_ai_field,
            "created_date": paper.get("created_date"),
            "updated_date": paper.get("updated_date"),
        }

        return paper_data

    except Exception as e:
        logger.error(f"Error transforming paper data: {e}", exc_info=True)
        return None


def transform_author_data(authorship: Dict, logger: logging.Logger) -> Optional[Dict]:
    """
    Transform JSON authorship data to author schema format.

    Args:
        authorship: Raw authorship data from JSON
        logger: Logger instance

    Returns:
        Transformed author data dictionary or None if invalid
    """
    try:
        author = authorship.get("author") or {}
        author_id = extract_id_from_url(author.get("id"))

        if not author_id:
            logger.warning(f"Authorship missing author ID")
            return None

        # Extract ORCID (remove URL prefix if present)
        orcid = author.get("orcid", "")
        if orcid and "orcid.org/" in orcid:
            orcid = orcid.split("orcid.org/")[-1]

        # Get primary institution and country
        institutions = authorship.get("institutions") or []
        countries = authorship.get("countries") or []

        primary_institution = (
            institutions[0].get("display_name") if institutions else None
        )
        primary_country = countries[0] if countries else None

        author_data = {
            "author_id": author_id,
            "display_name": author.get("display_name", "Unknown Author"),
            "orcid": orcid or None,
            "primary_institution": primary_institution,
            "primary_country": primary_country,
        }

        return author_data

    except Exception as e:
        logger.error(f"Error transforming author data: {e}", exc_info=True)
        return None


def transform_paper_author_data(
    paper_id: str, authorship: Dict, sequence: int, logger: logging.Logger
) -> Optional[Dict]:
    """
    Transform JSON authorship data to paper_authors schema format.

    Args:
        paper_id: Paper ID
        authorship: Raw authorship data from JSON
        sequence: Author sequence number (1-based)
        logger: Logger instance

    Returns:
        Transformed paper-author relationship data or None if invalid
    """
    try:
        author = authorship.get("author") or {}
        author_id = extract_id_from_url(author.get("id"))

        if not author_id:
            return None

        # Extract institution information
        institutions = authorship.get("institutions") or []
        institution_names = [
            inst.get("display_name")
            for inst in institutions
            if inst.get("display_name")
        ]
        institution_ids = [
            extract_id_from_url(inst.get("id"))
            for inst in institutions
            if inst.get("id")
        ]

        # Extract countries
        countries = authorship.get("countries") or []

        # Extract raw affiliation strings
        raw_affiliations = authorship.get("raw_affiliation_strings") or []

        paper_author_data = {
            "paper_id": paper_id,
            "author_id": author_id,
            "author_position": authorship.get("author_position"),
            "author_sequence": sequence,
            "is_corresponding": authorship.get("is_corresponding", False),
            "institution_names": institution_names if institution_names else None,
            "institution_ids": institution_ids if institution_ids else None,
            "countries": countries if countries else None,
            "raw_affiliation_strings": raw_affiliations if raw_affiliations else None,
        }

        return paper_author_data

    except Exception as e:
        logger.error(f"Error transforming paper-author data: {e}", exc_info=True)
        return None


def upsert_authors(
    conn, authors_data: List[Dict], stats: ImportStats, logger: logging.Logger
) -> None:
    """
    Insert or update authors in the database.

    Args:
        conn: Database connection
        authors_data: List of author data dictionaries
        stats: Statistics tracker
        logger: Logger instance
    """
    if not authors_data:
        return

    # Remove duplicates (same author may appear multiple times)
    unique_authors = {a["author_id"]: a for a in authors_data}
    authors_data = list(unique_authors.values())

    upsert_query = """
    INSERT INTO authors (
        author_id, display_name, orcid, primary_institution, primary_country
    ) VALUES %s
    ON CONFLICT (author_id) DO UPDATE SET
        display_name = COALESCE(EXCLUDED.display_name, authors.display_name),
        orcid = COALESCE(EXCLUDED.orcid, authors.orcid),
        primary_institution = COALESCE(EXCLUDED.primary_institution, authors.primary_institution),
        primary_country = COALESCE(EXCLUDED.primary_country, authors.primary_country),
        updated_at = CURRENT_TIMESTAMP
    RETURNING (xmax = 0) AS inserted;
    """

    try:
        with conn.cursor() as cursor:
            # Prepare values
            values = [
                (
                    a["author_id"],
                    a["display_name"],
                    a["orcid"],
                    a["primary_institution"],
                    a["primary_country"],
                )
                for a in authors_data
            ]

            # Execute batch insert/update
            execute_values(cursor, upsert_query, values, page_size=100)

            # Count inserts vs updates
            results = cursor.fetchall()
            for (inserted,) in results:
                if inserted:
                    stats.authors_inserted += 1
                else:
                    stats.authors_updated += 1

            conn.commit()
            logger.debug(f"Upserted {len(authors_data)} authors")

    except PostgresError as e:
        conn.rollback()
        stats.authors_failed += len(authors_data)
        logger.error(f"Error upserting authors: {e}")
        raise


def upsert_papers(
    conn, papers_data: List[Dict], stats: ImportStats, logger: logging.Logger
) -> None:
    """
    Insert or update papers in the database.

    Args:
        conn: Database connection
        papers_data: List of paper data dictionaries
        stats: Statistics tracker
        logger: Logger instance
    """
    if not papers_data:
        return

    upsert_query = """
    INSERT INTO papers (
        paper_id, doi, title, publication_year, publication_date, paper_type, language,
        journal_name, publisher, journal_issn, is_core_journal,
        is_open_access, oa_status, pdf_url, landing_page_url, license,
        author_count, first_author_name, corresponding_author_name,
        institution_count, country_count, first_institution, first_country,
        cited_by_count, referenced_works_count, fwci, citation_percentile,
        primary_topic, top_concept_1, top_concept_2, top_concept_3, keywords,
        is_retracted, is_paratext, has_abstract,
        ai_relevance_score, has_ai_field,
        created_date, updated_date
    ) VALUES %s
    ON CONFLICT (paper_id) DO UPDATE SET
        doi = COALESCE(EXCLUDED.doi, papers.doi),
        title = EXCLUDED.title,
        publication_year = COALESCE(EXCLUDED.publication_year, papers.publication_year),
        publication_date = COALESCE(EXCLUDED.publication_date, papers.publication_date),
        paper_type = COALESCE(EXCLUDED.paper_type, papers.paper_type),
        language = COALESCE(EXCLUDED.language, papers.language),
        journal_name = COALESCE(EXCLUDED.journal_name, papers.journal_name),
        publisher = COALESCE(EXCLUDED.publisher, papers.publisher),
        journal_issn = COALESCE(EXCLUDED.journal_issn, papers.journal_issn),
        is_core_journal = COALESCE(EXCLUDED.is_core_journal, papers.is_core_journal),
        is_open_access = COALESCE(EXCLUDED.is_open_access, papers.is_open_access),
        oa_status = COALESCE(EXCLUDED.oa_status, papers.oa_status),
        pdf_url = COALESCE(EXCLUDED.pdf_url, papers.pdf_url),
        landing_page_url = COALESCE(EXCLUDED.landing_page_url, papers.landing_page_url),
        license = COALESCE(EXCLUDED.license, papers.license),
        author_count = EXCLUDED.author_count,
        first_author_name = COALESCE(EXCLUDED.first_author_name, papers.first_author_name),
        corresponding_author_name = COALESCE(EXCLUDED.corresponding_author_name, papers.corresponding_author_name),
        institution_count = EXCLUDED.institution_count,
        country_count = EXCLUDED.country_count,
        first_institution = COALESCE(EXCLUDED.first_institution, papers.first_institution),
        first_country = COALESCE(EXCLUDED.first_country, papers.first_country),
        cited_by_count = EXCLUDED.cited_by_count,
        referenced_works_count = EXCLUDED.referenced_works_count,
        fwci = COALESCE(EXCLUDED.fwci, papers.fwci),
        citation_percentile = COALESCE(EXCLUDED.citation_percentile, papers.citation_percentile),
        primary_topic = COALESCE(EXCLUDED.primary_topic, papers.primary_topic),
        top_concept_1 = COALESCE(EXCLUDED.top_concept_1, papers.top_concept_1),
        top_concept_2 = COALESCE(EXCLUDED.top_concept_2, papers.top_concept_2),
        top_concept_3 = COALESCE(EXCLUDED.top_concept_3, papers.top_concept_3),
        keywords = COALESCE(EXCLUDED.keywords, papers.keywords),
        is_retracted = EXCLUDED.is_retracted,
        is_paratext = EXCLUDED.is_paratext,
        has_abstract = EXCLUDED.has_abstract,
        ai_relevance_score = COALESCE(EXCLUDED.ai_relevance_score, papers.ai_relevance_score),
        has_ai_field = COALESCE(EXCLUDED.has_ai_field, papers.has_ai_field),
        created_date = COALESCE(EXCLUDED.created_date, papers.created_date),
        updated_date = EXCLUDED.updated_date,
        ingested_at = CURRENT_TIMESTAMP
    RETURNING (xmax = 0) AS inserted;
    """

    try:
        with conn.cursor() as cursor:
            # Prepare values
            values = [
                (
                    p["paper_id"],
                    p["doi"],
                    p["title"],
                    p["publication_year"],
                    p["publication_date"],
                    p["paper_type"],
                    p["language"],
                    p["journal_name"],
                    p["publisher"],
                    p["journal_issn"],
                    p["is_core_journal"],
                    p["is_open_access"],
                    p["oa_status"],
                    p["pdf_url"],
                    p["landing_page_url"],
                    p["license"],
                    p["author_count"],
                    p["first_author_name"],
                    p["corresponding_author_name"],
                    p["institution_count"],
                    p["country_count"],
                    p["first_institution"],
                    p["first_country"],
                    p["cited_by_count"],
                    p["referenced_works_count"],
                    p["fwci"],
                    p["citation_percentile"],
                    p["primary_topic"],
                    p["top_concept_1"],
                    p["top_concept_2"],
                    p["top_concept_3"],
                    p["keywords"],
                    p["is_retracted"],
                    p["is_paratext"],
                    p["has_abstract"],
                    p["ai_relevance_score"],
                    p["has_ai_field"],
                    p["created_date"],
                    p["updated_date"],
                )
                for p in papers_data
            ]

            # Execute batch insert/update
            execute_values(cursor, upsert_query, values, page_size=100)

            # Count inserts vs updates
            results = cursor.fetchall()
            for (inserted,) in results:
                if inserted:
                    stats.papers_inserted += 1
                else:
                    stats.papers_updated += 1

            conn.commit()
            logger.debug(f"Upserted {len(papers_data)} papers")

    except PostgresError as e:
        conn.rollback()
        stats.papers_failed += len(papers_data)
        logger.error(f"Error upserting papers: {e}")
        raise


def upsert_paper_authors(
    conn, paper_authors_data: List[Dict], stats: ImportStats, logger: logging.Logger
) -> None:
    """
    Insert or update paper-author relationships in the database.

    Args:
        conn: Database connection
        paper_authors_data: List of paper-author relationship data
        stats: Statistics tracker
        logger: Logger instance
    """
    if not paper_authors_data:
        return

    # Deduplicate by (paper_id, author_id) - keep first occurrence
    # This handles cases where same author appears multiple times in a paper
    seen = set()
    unique_data = []
    duplicates_removed = 0

    for pa in paper_authors_data:
        key = (pa["paper_id"], pa["author_id"])
        if key not in seen:
            seen.add(key)
            unique_data.append(pa)
        else:
            duplicates_removed += 1

    if duplicates_removed > 0:
        logger.debug(
            f"Removed {duplicates_removed} duplicate paper-author relationships"
        )

    if not unique_data:
        return

    upsert_query = """
    INSERT INTO paper_authors (
        paper_id, author_id, author_position, author_sequence, is_corresponding,
        institution_names, institution_ids, countries, raw_affiliation_strings
    ) VALUES %s
    ON CONFLICT (paper_id, author_id) DO UPDATE SET
        author_position = EXCLUDED.author_position,
        author_sequence = EXCLUDED.author_sequence,
        is_corresponding = EXCLUDED.is_corresponding,
        institution_names = COALESCE(EXCLUDED.institution_names, paper_authors.institution_names),
        institution_ids = COALESCE(EXCLUDED.institution_ids, paper_authors.institution_ids),
        countries = COALESCE(EXCLUDED.countries, paper_authors.countries),
        raw_affiliation_strings = COALESCE(EXCLUDED.raw_affiliation_strings, paper_authors.raw_affiliation_strings),
        created_at = CURRENT_TIMESTAMP
    RETURNING (xmax = 0) AS inserted;
    """

    try:
        with conn.cursor() as cursor:
            # Prepare values
            values = [
                (
                    pa["paper_id"],
                    pa["author_id"],
                    pa["author_position"],
                    pa["author_sequence"],
                    pa["is_corresponding"],
                    pa["institution_names"],
                    pa["institution_ids"],
                    pa["countries"],
                    pa["raw_affiliation_strings"],
                )
                for pa in unique_data
            ]

            # Execute batch insert/update
            execute_values(cursor, upsert_query, values, page_size=100)

            # Count inserts vs updates
            results = cursor.fetchall()
            for (inserted,) in results:
                if inserted:
                    stats.paper_authors_inserted += 1
                else:
                    stats.paper_authors_updated += 1

            conn.commit()
            logger.debug(f"Upserted {len(unique_data)} paper-author relationships")

    except PostgresError as e:
        conn.rollback()
        stats.paper_authors_failed += len(unique_data)
        logger.error(f"Error upserting paper-authors: {e}")
        raise


def process_paper(
    paper: Dict, conn, stats: ImportStats, logger: logging.Logger
) -> bool:
    """
    Process a single paper and insert into database.

    Args:
        paper: Raw paper data from JSON
        conn: Database connection
        stats: Statistics tracker
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    try:
        # Transform paper data
        paper_data = transform_paper_data(paper, logger)
        if not paper_data:
            stats.papers_failed += 1
            return False

        paper_id = paper_data["paper_id"]
        logger.debug(f"Processing paper: {paper_id} - {paper_data['title'][:50]}...")

        # Transform authors data
        authorships = paper.get("authorships") or []
        authors_data = []
        paper_authors_data = []

        for idx, authorship in enumerate(authorships, start=1):
            # Transform author
            author_data = transform_author_data(authorship, logger)
            if author_data:
                authors_data.append(author_data)

            # Transform paper-author relationship
            paper_author_data = transform_paper_author_data(
                paper_id, authorship, idx, logger
            )
            if paper_author_data:
                paper_authors_data.append(paper_author_data)

        # Insert in correct order (authors -> papers -> paper_authors)
        # to satisfy foreign key constraints

        # 1. Upsert authors first
        if authors_data:
            upsert_authors(conn, authors_data, stats, logger)

        # 2. Upsert paper
        upsert_papers(conn, [paper_data], stats, logger)

        # 3. Upsert paper-author relationships
        if paper_authors_data:
            upsert_paper_authors(conn, paper_authors_data, stats, logger)

        stats.total_papers_processed += 1
        return True

    except Exception as e:
        stats.papers_failed += 1
        logger.error(f"Error processing paper: {e}", exc_info=True)
        return False


def load_json_file(filepath: str, logger: logging.Logger) -> Optional[List[Dict]]:
    """
    Load papers data from JSON file.

    Args:
        filepath: Path to JSON file
        logger: Logger instance

    Returns:
        List of paper dictionaries or None if error
    """
    try:
        logger.info(f"Loading JSON file: {filepath}")

        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.error(f"Expected JSON array, got {type(data)}")
            return None

        logger.info(f"Loaded {len(data)} papers from JSON")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}", exc_info=True)
        return None


def main():
    """Main execution function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Import research papers from JSON file into database"
    )
    parser.add_argument(
        "json_file", type=str, help="Path to JSON file containing paper data"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Directory for log files (default: logs)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Number of papers to process per batch (default: 1)",
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.log_dir)

    # Initialize statistics
    stats = ImportStats()

    logger.info("=" * 70)
    logger.info("PAPER IMPORT SCRIPT STARTED")
    logger.info("=" * 70)
    logger.info(f"JSON File: {args.json_file}")
    logger.info(f"Batch Size: {args.batch_size}")

    try:
        # Verify database connection
        logger.info("Verifying database connection...")
        config = DatabaseConfig()
        logger.info(f"Database: {config.database}")
        logger.info(f"Host: {config.host}")

        # Load JSON data
        papers = load_json_file(args.json_file, logger)
        if papers is None:
            logger.error("Failed to load JSON file")
            sys.exit(1)

        # Process papers
        logger.info(f"Starting to process {len(papers)} papers...")

        with get_connection() as conn:
            for idx, paper in enumerate(papers, start=1):
                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{len(papers)} papers processed")

                success = process_paper(paper, conn, stats, logger)

                if not success:
                    paper_id = extract_id_from_url(paper.get("id", "unknown"))
                    logger.warning(f"Failed to process paper {paper_id}")

        # Print summary
        logger.info(stats.get_summary())

        # Exit with appropriate code
        if stats.papers_failed > 0:
            logger.warning("Import completed with errors")
            sys.exit(1)
        else:
            logger.info("Import completed successfully!")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("\nImport interrupted by user")
        logger.info(stats.get_summary())
        sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        logger.info(stats.get_summary())
        sys.exit(1)


if __name__ == "__main__":
    main()
