"""
Deploy Database Schema Script

This script deploys the complete database schema (tables, indexes, triggers, views)
to the PostgreSQL database using the database.py connection module.

Usage:
    python database/deploy_schema.py

    Or from root:
    python -m database.deploy_schema
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import database module
script_dir = Path(__file__).parent
parent_dir = script_dir.parent
sys.path.insert(0, str(parent_dir))

# Import from the database folder
sys.path.insert(0, str(script_dir))

from database import get_connection, DatabaseConfig
from psycopg2 import Error as PostgresError


def read_schema_file(schema_path: str = "database/schema.sql") -> str:
    """
    Read the SQL schema file.

    Args:
        schema_path: Path to the schema.sql file

    Returns:
        str: Contents of the schema file

    Raises:
        FileNotFoundError: If schema file doesn't exist
    """
    schema_file = Path(schema_path)

    if not schema_file.exists():
        raise FileNotFoundError(
            f"Schema file not found: {schema_path}\n"
            f"Please ensure schema.sql exists in the database folder."
        )

    print(f"Reading schema from: {schema_file}")
    with open(schema_file, "r", encoding="utf-8") as f:
        return f.read()


def deploy_schema(schema_sql: str, dry_run: bool = False) -> bool:
    """
    Deploy the schema to the database.

    Args:
        schema_sql: SQL schema content
        dry_run: If True, only validate connection without executing

    Returns:
        bool: True if successful, False otherwise
    """
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made to the database")
        print(f"Schema size: {len(schema_sql)} characters")
        print(f"Schema lines: {schema_sql.count(chr(10)) + 1}")
        return True

    try:
        print("\n" + "=" * 70)
        print("DEPLOYING DATABASE SCHEMA")
        print("=" * 70)

        # Connect to database
        print("\n📡 Connecting to database...")
        with get_connection() as conn:
            print("✓ Connected successfully")

            # Create cursor
            with conn.cursor() as cursor:
                print("\n🔨 Executing schema SQL...")
                print("   This will:")
                print("   - Drop existing tables (if any)")
                print("   - Create 3 tables: papers, authors, paper_authors")
                print("   - Create 39 indexes")
                print("   - Create 1 trigger function")
                print("   - Create 3 views")

                # Execute the schema
                cursor.execute(schema_sql)

                # Commit the transaction
                conn.commit()
                print("\n✓ Schema executed successfully")

                # Verify tables were created
                print("\n📊 Verifying deployment...")
                cursor.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """
                )
                tables = cursor.fetchall()

                print(f"\n✓ Tables created ({len(tables)}):")
                for table in tables:
                    print(f"   • {table[0]}")

                # Verify indexes
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM pg_indexes 
                    WHERE schemaname = 'public';
                """
                )
                index_count = cursor.fetchone()[0]
                print(f"\n✓ Indexes created: {index_count}")

                # Verify views
                cursor.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.views 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """
                )
                views = cursor.fetchall()

                print(f"\n✓ Views created ({len(views)}):")
                for view in views:
                    print(f"   • {view[0]}")

                # Verify triggers
                cursor.execute(
                    """
                    SELECT trigger_name, event_object_table
                    FROM information_schema.triggers
                    WHERE trigger_schema = 'public'
                    ORDER BY trigger_name;
                """
                )
                triggers = cursor.fetchall()

                print(f"\n✓ Triggers created ({len(triggers)}):")
                for trigger in triggers:
                    print(f"   • {trigger[0]} on {trigger[1]}")

                print("\n" + "=" * 70)
                print("✓ SCHEMA DEPLOYMENT COMPLETED SUCCESSFULLY")
                print("=" * 70)

                return True

    except PostgresError as e:
        print("\n" + "=" * 70)
        print("✗ DATABASE ERROR")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nDeployment failed. Please check:")
        print("  1. Database credentials in .env file")
        print("  2. Database connection is working")
        print("  3. SQL syntax in schema.sql")
        return False

    except Exception as e:
        print("\n" + "=" * 70)
        print("✗ UNEXPECTED ERROR")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main execution function."""
    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 70)
    print("DATABASE SCHEMA DEPLOYMENT TOOL")
    print("=" * 70)

    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv

    try:
        # Test database configuration
        print("\n📋 Testing database configuration...")
        config = DatabaseConfig()
        print(f"✓ Configuration loaded")
        print(f"   Host: {config.host}")
        print(f"   Database: {config.database}")
        print(f"   User: {config.user}")

        # Read schema file
        print("\n📄 Reading schema file...")
        schema_sql = read_schema_file("database/schema.sql")
        print(f"✓ Schema loaded ({len(schema_sql)} characters)")

        # Deploy schema
        success = deploy_schema(schema_sql, dry_run=dry_run)

        if success:
            if not dry_run:
                print("\n🎉 Database is ready to use!")
                print("\nNext steps:")
                print("  1. Create an ETL script to load data from JSON files")
                print("  2. Insert papers into the 'papers' table")
                print("  3. Insert authors into the 'authors' table")
                print("  4. Insert relationships into the 'paper_authors' table")
                print("  5. Author metrics will auto-update via triggers")
            return 0
        else:
            print("\n✗ Deployment failed. Please fix errors and try again.")
            return 1

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        return 1

    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nPlease ensure:")
        print("  1. .env file exists in the project root")
        print("  2. All required variables are set:")
        print("     - DB_HOST")
        print("     - DB_NAME")
        print("     - DB_USER")
        print("     - DB_PASSWORD")
        print("\nSee env.template for an example.")
        return 1

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
