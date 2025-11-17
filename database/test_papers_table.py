#!/usr/bin/env python3
"""
Data Quality Tests for Papers Table

This script executes comprehensive SQL data quality tests on the papers table,
with configurable thresholds and detailed failure reports showing counts and
sample failing records.

Usage:
    python test_papers_table.py [--config CONFIG_FILE] [--output OUTPUT_FILE]

Features:
- 18 comprehensive data quality tests across 6 categories
- Configurable thresholds via YAML config file
- Detailed reporting with sample failing records
- Exit codes: 0 = all pass, 1 = failures detected
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml

import psycopg2
from psycopg2 import Error as PostgresError

# Import database module from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection, DatabaseConfig


class TestResult:
    """Represents the result of a single test."""

    def __init__(self, test_name: str, category: str, description: str):
        self.test_name = test_name
        self.category = category
        self.description = description
        self.passed = False
        self.failure_count = 0
        self.sample_records = []
        self.error_message = None
        self.execution_time = 0.0

    def __str__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.test_name}: {self.failure_count} failures"


class TestRunner:
    """Main test runner class."""

    def __init__(self, config_path: str = "test_config.yaml"):
        """Initialize test runner with configuration."""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.results = []
        self.start_time = datetime.now()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {config_path} not found. Using defaults.")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            sys.exit(1)

    def _get_default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "suspicious_citation_threshold": 100000,
            "retracted_update_window_days": 30,
            "max_duplicate_dois": 0,
            "max_sample_records": 10,
            "show_samples_for_passing_tests": False,
            "continue_on_failure": True,
            "output": {
                "format": "detailed",
                "include_queries": False,
                "save_to_file": True,
                "output_file": "test_results.txt",
                "include_timestamps": True,
            },
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("test_papers_table")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_sql_file(self, filepath: str) -> List[str]:
        """Load SQL queries from file and split into individual queries."""
        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Split by test sections (looking for test comments)
            queries = []
            current_query = []
            in_test_section = False

            for line in content.split("\n"):
                line_stripped = line.strip()

                # Start of a new test section
                if line_stripped.startswith("-- Test "):
                    if current_query and in_test_section:
                        # Save previous test
                        query_text = "\n".join(current_query).strip()
                        if query_text and "SELECT" in query_text:
                            queries.append(query_text)
                    current_query = []
                    in_test_section = True

                # Add line to current query if we're in a test section
                if in_test_section:
                    current_query.append(line)

                # End of test section (next test or end of file)
                if (
                    line_stripped.startswith(
                        "-- ============================================================================"
                    )
                    and current_query
                    and in_test_section
                ):
                    query_text = "\n".join(current_query).strip()
                    if query_text and "SELECT" in query_text:
                        queries.append(query_text)
                    current_query = []
                    in_test_section = False

            # Add the last query if exists
            if current_query and in_test_section:
                query_text = "\n".join(current_query).strip()
                if query_text and "SELECT" in query_text:
                    queries.append(query_text)

            return queries

        except FileNotFoundError:
            self.logger.error(f"SQL file not found: {filepath}")
            return []
        except Exception as e:
            self.logger.error(f"Error loading SQL file {filepath}: {e}")
            return []

    def _execute_test_query(self, conn, query: str) -> Tuple[int, List[Dict]]:
        """Execute a test query and return failure count and sample records."""
        try:
            with conn.cursor() as cursor:
                # Split query into count query and sample query
                query_parts = query.split("SELECT")

                if len(query_parts) < 3:
                    # Simple query, execute as-is
                    cursor.execute(query)
                    result = cursor.fetchone()
                    return result[0] if result else 0, []

                # Extract count query (first SELECT after comments)
                count_query_start = query.find("SELECT")
                sample_query_start = query.find("SELECT", count_query_start + 1)

                if sample_query_start == -1:
                    # Only count query
                    cursor.execute(query)
                    result = cursor.fetchone()
                    return result[0] if result else 0, []

                # Extract count query
                count_query = query[count_query_start:sample_query_start].strip()
                if count_query.endswith(";"):
                    count_query = count_query[:-1]

                # Execute count query
                cursor.execute(count_query)
                count_result = cursor.fetchone()
                failure_count = count_result[0] if count_result else 0

                # If there are failures, get sample records
                sample_records = []
                if failure_count > 0:
                    sample_query = query[sample_query_start:].strip()
                    if sample_query.endswith(";"):
                        sample_query = sample_query[:-1]

                    cursor.execute(sample_query)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()

                    sample_records = [dict(zip(columns, row)) for row in rows][
                        : self.config.get("max_sample_records", 10)
                    ]

                return failure_count, sample_records

        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise

    def _run_test_category(
        self, conn, category: str, sql_file: str
    ) -> List[TestResult]:
        """Run all tests in a category."""
        self.logger.info(f"Running {category} tests...")

        sql_path = Path(__file__).parent / "tests" / sql_file
        queries = self._load_sql_file(str(sql_path))

        if not queries:
            self.logger.warning(f"No queries found in {sql_file}")
            return []

        results = []

        # Parse test information from SQL comments
        test_info = self._parse_test_info(str(sql_path))

        for i, query in enumerate(queries):
            if not query.strip():
                continue

            # Get test info for this query
            test_name = f"{category}_test_{i+1}"
            description = f"Test {i+1} in {category}"

            if i < len(test_info):
                test_name = test_info[i].get("name", test_name)
                description = test_info[i].get("description", description)

            result = TestResult(test_name, category, description)

            try:
                start_time = datetime.now()

                # Apply configuration parameters to query
                modified_query = self._apply_config_to_query(query)

                failure_count, sample_records = self._execute_test_query(
                    conn, modified_query
                )

                result.execution_time = (datetime.now() - start_time).total_seconds()
                result.failure_count = failure_count
                result.sample_records = sample_records
                result.passed = failure_count == 0

                self.logger.info(f"  {result}")

            except Exception as e:
                result.error_message = str(e)
                result.passed = False
                self.logger.error(f"  [ERROR] {test_name}: {e}")

            results.append(result)

            # Stop on failure if configured
            if not result.passed and not self.config.get("continue_on_failure", True):
                break

        return results

    def _parse_test_info(self, sql_file: str) -> List[Dict]:
        """Parse test information from SQL file comments."""
        test_info = []

        try:
            with open(sql_file, "r") as f:
                content = f.read()

            # Look for test sections
            lines = content.split("\n")
            current_test = {}

            for line in lines:
                line = line.strip()
                if line.startswith("-- Test "):
                    if current_test:
                        test_info.append(current_test)
                    current_test = {
                        "name": line.replace("-- Test ", "").replace(":", "").strip(),
                        "description": "",
                    }
                elif (
                    line.startswith("--")
                    and current_test
                    and not current_test.get("description")
                ):
                    # First comment after test header is description
                    desc = line.replace("--", "").strip()
                    if desc and not desc.startswith("="):
                        current_test["description"] = desc

            if current_test:
                test_info.append(current_test)

        except Exception as e:
            self.logger.warning(f"Could not parse test info from {sql_file}: {e}")

        return test_info

    def _apply_config_to_query(self, query: str) -> str:
        """Apply configuration parameters to SQL query."""
        # Replace configurable thresholds
        query = query.replace(
            "100000", str(self.config.get("suspicious_citation_threshold", 100000))
        )
        query = query.replace(
            "INTERVAL '30 days'",
            f"INTERVAL '{self.config.get('retracted_update_window_days', 30)} days'",
        )

        return query

    def run_all_tests(self) -> bool:
        """Run all test categories and return True if all pass."""
        self.logger.info("Starting data quality tests for papers table...")
        self.logger.info(f"Configuration loaded from: test_config.yaml")

        try:
            # Verify database connection
            config = DatabaseConfig()
            self.logger.info(f"Database: {config.database}")
            self.logger.info(f"Host: {config.host}")

            with get_connection() as conn:
                # Test categories and their SQL files
                test_categories = [
                    ("Data Completeness", "01_data_completeness.sql"),
                    ("Data Validity", "02_data_validity.sql"),
                    ("Business Logic", "03_business_logic.sql"),
                    ("Data Quality", "04_data_quality.sql"),
                    ("Referential Integrity", "05_referential_integrity.sql"),
                    ("Timestamps & Metadata", "06_timestamps_metadata.sql"),
                ]

                # Run each category
                for category, sql_file in test_categories:
                    category_results = self._run_test_category(conn, category, sql_file)
                    self.results.extend(category_results)

        except Exception as e:
            self.logger.error(f"Fatal error during test execution: {e}")
            return False

        # Generate and save report
        self._generate_report()

        # Return True if all tests passed
        return all(result.passed for result in self.results)

    def _generate_report(self):
        """Generate detailed test report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        total_failures = sum(r.failure_count for r in self.results)

        duration = (datetime.now() - self.start_time).total_seconds()

        # Generate report content
        report_lines = [
            "=" * 80,
            "DATA QUALITY TEST REPORT - PAPERS TABLE",
            "=" * 80,
            f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {duration:.2f} seconds",
            f"Total Tests: {total_tests}",
            f"Passed: {passed_tests}",
            f"Failed: {failed_tests}",
            f"Total Data Quality Issues: {total_failures}",
            "",
        ]

        # Group results by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        # Report by category
        for category, results in categories.items():
            category_passed = sum(1 for r in results if r.passed)
            category_total = len(results)
            category_failures = sum(r.failure_count for r in results)

            report_lines.extend(
                [
                    f"{category.upper()} ({category_passed}/{category_total} passed, {category_failures} issues)",
                    "-" * 60,
                ]
            )

            for result in results:
                status = "PASS" if result.passed else "FAIL"
                report_lines.append(f"[{status}] {result.test_name}")
                report_lines.append(f"  Description: {result.description}")
                report_lines.append(f"  Issues Found: {result.failure_count}")
                report_lines.append(f"  Execution Time: {result.execution_time:.3f}s")

                if result.error_message:
                    report_lines.append(f"  Error: {result.error_message}")

                # Show sample records for failures
                if not result.passed and result.sample_records:
                    report_lines.append("  Sample Failing Records:")
                    for i, record in enumerate(result.sample_records[:5], 1):
                        record_str = ", ".join(
                            [f"{k}: {v}" for k, v in record.items() if v is not None]
                        )
                        report_lines.append(f"    {i}. {record_str}")

                report_lines.append("")

        report_lines.extend(
            [
                "=" * 80,
                "SUMMARY",
                "=" * 80,
                f"Overall Status: {'PASS' if failed_tests == 0 else 'FAIL'}",
                (
                    f"Tests Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)"
                    if total_tests > 0
                    else "Tests Passed: 0/0 (0%)"
                ),
                f"Data Quality Issues: {total_failures}",
                "",
            ]
        )

        if failed_tests > 0:
            report_lines.extend(
                [
                    "RECOMMENDATIONS:",
                    "- Review failing tests and investigate root causes",
                    "- Check data import processes for validation gaps",
                    "- Consider adding constraints or triggers to prevent issues",
                    "- Update data cleaning procedures as needed",
                    "",
                ]
            )

        report_content = "\n".join(report_lines)

        # Print to console
        print(report_content)

        # Save to file if configured
        if self.config.get("output", {}).get("save_to_file", True):
            output_file = self.config.get("output", {}).get(
                "output_file", "test_results.txt"
            )
            try:
                with open(output_file, "w") as f:
                    f.write(report_content)
                self.logger.info(f"Report saved to: {output_file}")
            except Exception as e:
                self.logger.error(f"Could not save report to file: {e}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run data quality tests on papers table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_papers_table.py
  python test_papers_table.py --config custom_config.yaml
  python test_papers_table.py --output results.txt
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        default="test_config.yaml",
        help="Path to configuration file (default: test_config.yaml)",
    )

    parser.add_argument(
        "--output", "-o", help="Output file for results (overrides config file setting)"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    try:
        # Initialize test runner
        runner = TestRunner(args.config)

        if args.verbose:
            runner.logger.setLevel(logging.DEBUG)

        # Override output file if specified
        if args.output:
            runner.config.setdefault("output", {})["output_file"] = args.output

        # Run all tests
        all_passed = runner.run_all_tests()

        # Exit with appropriate code
        if all_passed:
            runner.logger.info("All tests passed!")
            sys.exit(0)
        else:
            runner.logger.warning("Some tests failed. Check the report for details.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
