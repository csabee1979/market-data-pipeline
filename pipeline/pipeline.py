#!/usr/bin/env python3
"""
Research Papers Data Pipeline

This script consolidates the entire data pipeline workflow:
1. Queries API to get recent papers
2. Creates the DB tables if needed
3. Uploads data to the database
4. Runs quality tests

Usage:
    python pipeline/pipeline.py [--config CONFIG_FILE] [--dry-run]

Features:
- Standalone pipeline orchestration
- Configurable via YAML config file
- Comprehensive logging and error handling
- Quality testing integration
- Exit codes: 0 = success, 1 = failure
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Optional
import yaml

# Import database module
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "database")
)
from database import get_connection, DatabaseConfig

# Import existing modules from database directory
from deploy_schema import deploy_schema, read_schema_file
from import_papers import (
    setup_logging,
    load_json_file,
    process_paper,
    ImportStats,
    reset_doi_tracking,
)
from test_papers_table import TestRunner

# Import paper fetcher from same directory
import fetch_ai_papers


class PipelineConfig:
    """Configuration management for the pipeline."""

    def __init__(self, config_path: str = "database/pipeline_config.yaml"):
        """Initialize configuration from YAML file."""
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_path} not found. Using defaults.")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            sys.exit(1)

    def _get_default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "api": {
                "days_back": 3,  # Number of days to look back for papers
                "min_ai_score": 0.7,  # Minimum AI relevance score
                "output_dir": "temp",  # Directory for temporary files
            },
            "database": {"schema_file": "database/schema.sql", "deploy_schema": True},
            "testing": {"run_tests": True, "config_file": "database/test_config.yaml"},
            "logging": {"level": "INFO", "log_dir": "logs"},
        }

    def get(self, key: str, default=None):
        """Get configuration value."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value


class PipelineStats:
    """Track pipeline execution statistics."""

    def __init__(self):
        self.start_time = datetime.now()
        self.papers_fetched = 0
        self.papers_processed = 0
        self.schema_deployed = False
        self.tests_passed = 0
        self.tests_failed = 0
        self.errors = []

    def add_error(self, stage: str, error: str):
        """Add an error to the tracking."""
        self.errors.append(f"[{stage}] {error}")

    def get_summary(self) -> str:
        """Generate pipeline execution summary."""
        duration = (datetime.now() - self.start_time).total_seconds()
        return f"""
{'='*70}
PIPELINE EXECUTION SUMMARY
{'='*70}
Duration: {duration:.2f} seconds
Papers Fetched: {self.papers_fetched}
Papers Processed: {self.papers_processed}
Schema Deployed: {'Yes' if self.schema_deployed else 'No'}
Tests Passed: {self.tests_passed}
Tests Failed: {self.tests_failed}
Errors: {len(self.errors)}

{'Errors:' if self.errors else ''}
{chr(10).join(f'  - {error}' for error in self.errors)}
{'='*70}
"""


class ResearchPapersPipeline:
    """Main pipeline orchestration class."""

    def __init__(self, config_path: str = "pipeline_config.yaml"):
        """Initialize the pipeline."""
        self.config = PipelineConfig(config_path)
        self.stats = PipelineStats()
        self.logger = self._setup_logging()
        self.temp_files = []  # Track temporary files for cleanup

    def _setup_logging(self) -> logging.Logger:
        """Setup pipeline logging."""
        log_level = self.config.get("logging.level", "INFO")
        log_dir = self.config.get("logging.log_dir", "logs")

        # Use existing setup_logging function but customize for pipeline
        logger = setup_logging(log_dir)
        logger.name = "pipeline"

        # Set log level
        if hasattr(logging, log_level):
            logger.setLevel(getattr(logging, log_level))

        return logger

    def fetch_papers_from_api(self) -> Optional[str]:
        """
        Fetch recent AI papers using the existing fetch_ai_papers module.

        Returns:
            Path to JSON file with fetched papers, or None if failed
        """
        self.logger.info("=" * 50)
        self.logger.info("STAGE 1: FETCHING AI PAPERS FROM API")
        self.logger.info("=" * 50)

        try:
            days_back = self.config.get("api.days_back", 3)
            min_ai_score = self.config.get("api.min_ai_score", 0.7)
            output_dir = self.config.get("api.output_dir", "temp")

            self.logger.info("Fetching AI papers from last %d days", days_back)
            self.logger.info("Minimum AI relevance score: %s", min_ai_score)
            self.logger.info("Output directory: %s", output_dir)

            # Step 1: Find the AI concept using existing function
            self.logger.info("Finding AI concept...")
            concept_id = fetch_ai_papers.find_ai_concept()
            if not concept_id:
                error_msg = "Failed to find AI concept"
                self.logger.error(error_msg)
                self.stats.add_error("API_FETCH", error_msg)
                return None

            # Step 2: Fetch AI papers using existing function
            self.logger.info("Fetching AI papers...")
            papers = fetch_ai_papers.fetch_recent_ai_papers(concept_id, days=days_back)

            if not papers:
                self.logger.warning("No AI papers found in the specified time range")
                # Create empty file for consistency
                papers = []

            self.stats.papers_fetched = len(papers)
            self.logger.info("Successfully fetched %d AI papers", len(papers))

            # Step 3: Save to JSON file using existing function
            json_file_path = fetch_ai_papers.save_to_json(papers, output_dir)
            if not json_file_path:
                error_msg = "Failed to save papers to JSON file"
                self.logger.error(error_msg)
                self.stats.add_error("API_FETCH", error_msg)
                return None

            # Track the file for cleanup if it's in temp directory
            if output_dir == "temp":
                self.temp_files.append(json_file_path)

            self.logger.info("Papers saved to: %s", json_file_path)
            return json_file_path

        except Exception as e:
            error_msg = f"Failed to fetch papers from API: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.stats.add_error("API_FETCH", error_msg)
            return None

    def ensure_database_schema(self, dry_run: bool = False) -> bool:
        """
        Ensure database schema is deployed.

        Args:
            dry_run: If True, only validate without making changes

        Returns:
            True if successful, False otherwise
        """
        self.logger.info("=" * 50)
        self.logger.info("STAGE 2: ENSURING DATABASE SCHEMA")
        self.logger.info("=" * 50)

        try:
            if not self.config.get("database.deploy_schema", True):
                self.logger.info("Schema deployment disabled in config")
                return True

            schema_file = self.config.get("database.schema_file", "database/schema.sql")

            # Read schema file
            self.logger.info("Reading schema from: %s", schema_file)
            schema_sql = read_schema_file(schema_file)

            # Deploy schema
            success = deploy_schema(schema_sql, dry_run=dry_run)

            if success:
                self.stats.schema_deployed = True
                self.logger.info("Database schema ensured successfully")
            else:
                error_msg = "Failed to deploy database schema"
                self.logger.error(error_msg)
                self.stats.add_error("SCHEMA_DEPLOY", error_msg)

            return success

        except Exception as e:
            error_msg = f"Error ensuring database schema: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.stats.add_error("SCHEMA_DEPLOY", error_msg)
            return False

    def load_papers_to_database(self, json_file: str, dry_run: bool = False) -> bool:
        """
        Load papers from JSON file to database.

        Args:
            json_file: Path to JSON file with papers
            dry_run: If True, only validate without making changes

        Returns:
            True if successful, False otherwise
        """
        self.logger.info("=" * 50)
        self.logger.info("STAGE 3: LOADING PAPERS TO DATABASE")
        self.logger.info("=" * 50)

        if dry_run:
            self.logger.info("DRY RUN MODE - No data will be loaded")
            # Just validate the JSON file
            papers = load_json_file(json_file, self.logger)
            if papers:
                self.logger.info(f"Validated {len(papers)} papers in JSON file")
                return True
            return False

        try:
            # Reset DOI tracking for this batch
            reset_doi_tracking()

            # Load papers from JSON
            papers = load_json_file(json_file, self.logger)
            if not papers:
                error_msg = "Failed to load papers from JSON file"
                self.logger.error(error_msg)
                self.stats.add_error("DATA_LOAD", error_msg)
                return False

            # Initialize import statistics
            import_stats = ImportStats()

            self.logger.info("Processing %d papers...", len(papers))

            # Process papers using existing logic
            with get_connection() as conn:
                for idx, paper in enumerate(papers, start=1):
                    if idx % 50 == 0:
                        self.logger.info(
                            "Progress: %d/%d papers processed", idx, len(papers)
                        )

                    success = process_paper(paper, conn, import_stats, self.logger)

                    if success:
                        self.stats.papers_processed += 1
                    else:
                        paper_id = paper.get("id", "unknown")
                        self.logger.warning("Failed to process paper %s", paper_id)

            # Log import summary
            self.logger.info(import_stats.get_summary())

            if import_stats.papers_failed > 0:
                self.logger.warning(
                    "Data loading completed with %d failures",
                    import_stats.papers_failed,
                )
            else:
                self.logger.info("Data loading completed successfully")

            return True

        except Exception as e:
            error_msg = f"Error loading papers to database: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.stats.add_error("DATA_LOAD", error_msg)
            return False

    def run_quality_tests(self, dry_run: bool = False) -> bool:
        """
        Run data quality tests on the loaded data.

        Args:
            dry_run: If True, only validate test configuration

        Returns:
            True if all tests pass, False otherwise
        """
        self.logger.info("=" * 50)
        self.logger.info("STAGE 4: RUNNING QUALITY TESTS")
        self.logger.info("=" * 50)

        try:
            if not self.config.get("testing.run_tests", True):
                self.logger.info("Quality testing disabled in config")
                return True

            if dry_run:
                self.logger.info("DRY RUN MODE - Tests will not be executed")
                test_config = self.config.get(
                    "testing.config_file", "database/test_config.yaml"
                )
                self.logger.info("Test configuration: %s", test_config)
                return True

            # Initialize test runner
            test_config_file = self.config.get(
                "testing.config_file", "database/test_config.yaml"
            )
            test_runner = TestRunner(test_config_file)

            # Run all tests
            all_passed = test_runner.run_all_tests()

            # Update statistics
            for result in test_runner.results:
                if result.passed:
                    self.stats.tests_passed += 1
                else:
                    self.stats.tests_failed += 1

            if all_passed:
                self.logger.info("All quality tests passed!")
            else:
                self.logger.warning(
                    "Some quality tests failed. Check test report for details."
                )
                self.stats.add_error(
                    "QUALITY_TESTS", f"{self.stats.tests_failed} tests failed"
                )

            return all_passed

        except Exception as e:
            error_msg = f"Error running quality tests: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.stats.add_error("QUALITY_TESTS", error_msg)
            return False

    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    self.logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                self.logger.warning("Could not clean up %s: %s", temp_file, e)

    def run_pipeline(
        self,
        dry_run: bool = False,
        skip_quality_tests: bool = False,
        force_store: bool = False,
    ) -> bool:
        """
        Run the complete data pipeline.

        Args:
            dry_run: If True, validate configuration and connections without making changes
            skip_quality_tests: If True, skip quality test execution (overrides config)
            force_store: If True, store papers even if quality tests fail

        Returns:
            True if pipeline completed successfully, False otherwise
        """
        self.logger.info("=" * 70)
        self.logger.info("RESEARCH PAPERS DATA PIPELINE STARTED")
        self.logger.info("=" * 70)
        self.logger.info("Configuration: %s", self.config.config_path)
        self.logger.info("Dry run mode: %s", dry_run)
        self.logger.info("Skip quality tests: %s", skip_quality_tests)
        self.logger.info("Force store: %s", force_store)

        try:
            # Verify database connection
            self.logger.info("Verifying database connection...")
            db_config = DatabaseConfig()
            self.logger.info("Database: %s @ %s", db_config.database, db_config.host)

            # Stage 1: Fetch papers from API
            json_file = self.fetch_papers_from_api()
            if not json_file:
                self.logger.error("Pipeline failed at API fetch stage")
                return False

            # Stage 2: Ensure database schema
            if not self.ensure_database_schema(dry_run=dry_run):
                self.logger.error("Pipeline failed at schema deployment stage")
                return False

            # Stage 3: Load papers to database
            if not self.load_papers_to_database(json_file, dry_run=dry_run):
                self.logger.error("Pipeline failed at data loading stage")
                return False

            # Stage 4: Run quality tests (if not skipped)
            should_skip_tests = skip_quality_tests or self.config.get(
                "execution.skip_quality_tests", False
            )

            if should_skip_tests:
                self.logger.info("=" * 50)
                self.logger.info("STAGE 4: QUALITY TESTS SKIPPED")
                self.logger.info("=" * 50)
                self.logger.info("Quality tests skipped as requested")
            else:
                tests_passed = self.run_quality_tests(dry_run=dry_run)

                # Check if we should force store even with test failures
                should_force_store = force_store or self.config.get(
                    "execution.force_store", False
                )

                if not tests_passed and not should_force_store:
                    self.logger.error("Pipeline failed at quality testing stage")
                    self.logger.info(
                        "Use --force-store to store data despite test failures"
                    )
                    return False
                elif not tests_passed and should_force_store:
                    self.logger.warning(
                        "Quality tests failed but force_store is enabled - continuing"
                    )
                    self.logger.warning(
                        "Data has been stored despite quality test failures"
                    )

            # Pipeline completed successfully
            self.logger.info("=" * 70)
            self.logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 70)
            self.logger.info(self.stats.get_summary())

            return True

        except KeyboardInterrupt:
            self.logger.warning("Pipeline interrupted by user")
            return False

        except Exception as e:
            error_msg = f"Unexpected pipeline error: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.stats.add_error("PIPELINE", error_msg)
            return False

        finally:
            # Always cleanup temporary files
            self.cleanup()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Research Papers Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline Stages:
  1. Fetch recent papers from OpenAlex API
  2. Ensure database schema is deployed
  3. Load papers data into database
  4. Run comprehensive quality tests (optional)

Examples:
  python pipeline.py
  python pipeline.py --config custom_config.yaml
  python pipeline.py --dry-run
  python pipeline.py --skip-quality-tests
  python pipeline.py --force-store
  python pipeline.py --skip-quality-tests --force-store
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        default="pipeline/pipeline_config.yaml",
        help="Path to configuration file (default: pipeline/pipeline_config.yaml)",
    )

    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Validate configuration and connections without making changes",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--skip-quality-tests",
        action="store_true",
        help="Skip quality test execution (overrides config file setting)",
    )

    parser.add_argument(
        "--force-store",
        action="store_true",
        help="Force storing papers in database even if quality tests fail",
    )

    args = parser.parse_args()

    try:
        # Initialize pipeline
        pipeline = ResearchPapersPipeline(args.config)

        if args.verbose:
            pipeline.logger.setLevel(logging.DEBUG)

        # Run pipeline with command-line overrides
        success = pipeline.run_pipeline(
            dry_run=args.dry_run,
            skip_quality_tests=args.skip_quality_tests,
            force_store=args.force_store,
        )

        # Exit with appropriate code
        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
