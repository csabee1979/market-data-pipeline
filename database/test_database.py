"""
Test script for database connection and operations.

This script tests:
1. Loading configuration from .env file
2. Connecting to the Neon PostgreSQL database
3. Running basic queries
4. Verifying connection works properly
"""

import sys
from database import (
    DatabaseConfig,
    DatabaseConnection,
    verify_connection,
    get_connection,
    execute_query,
)

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def test_configuration():
    """Test loading database configuration."""
    print("\n" + "=" * 60)
    print("TEST 1: Loading Database Configuration")
    print("=" * 60)

    try:
        config = DatabaseConfig()
        print("✓ Configuration loaded successfully")
        print(f"  Host: {config.host}")
        print(f"  Database: {config.database}")
        print(f"  User: {config.user}")
        print(
            f"  Password: {'*' * len(config.password) if config.password else 'NOT SET'}"
        )
        print(f"  SSL Mode: {config.sslmode}")
        return True
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False


def test_connection():
    """Test basic database connection."""
    print("\n" + "=" * 60)
    print("TEST 2: Database Connection")
    print("=" * 60)

    success, message = verify_connection()
    print(message)
    return success


def test_context_manager():
    """Test using the connection context manager."""
    print("\n" + "=" * 60)
    print("TEST 3: Context Manager Connection")
    print("=" * 60)

    try:
        with get_connection() as conn:
            print("✓ Connection established using context manager")

            with conn.cursor() as cursor:
                # Test query 1: Get database size
                cursor.execute(
                    """
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size;
                """
                )
                db_size = cursor.fetchone()[0]
                print(f"  Database size: {db_size}")

                # Test query 2: Get number of tables
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public';
                """
                )
                table_count = cursor.fetchone()[0]
                print(f"  Number of tables in 'public' schema: {table_count}")

                # Test query 3: List all tables
                cursor.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """
                )
                tables = cursor.fetchall()
                if tables:
                    print(f"  Tables: {', '.join([t[0] for t in tables])}")
                else:
                    print("  Tables: (no tables found in public schema)")

        print("✓ Context manager test completed successfully")
        return True

    except Exception as e:
        print(f"✗ Context manager test failed: {e}")
        return False


def test_execute_query():
    """Test the execute_query helper function."""
    print("\n" + "=" * 60)
    print("TEST 4: Execute Query Helper Function")
    print("=" * 60)

    try:
        # Test a simple query
        result = execute_query("SELECT NOW() as current_time;")
        current_time = result[0][0]
        print(f"✓ Query executed successfully")
        print(f"  Current database time: {current_time}")

        # Test a parameterized query
        result = execute_query(
            "SELECT %s::text as message, %s::int as number;", ("Hello from test!", 42)
        )
        message, number = result[0]
        print(f"✓ Parameterized query executed successfully")
        print(f"  Message: {message}")
        print(f"  Number: {number}")

        return True

    except Exception as e:
        print(f"✗ Execute query test failed: {e}")
        return False


def run_all_tests():
    """Run all database tests."""
    print("\n" + "=" * 60)
    print("DATABASE CONNECTION TEST SUITE")
    print("=" * 60)

    tests = [
        ("Configuration", test_configuration),
        ("Connection", test_connection),
        ("Context Manager", test_context_manager),
        ("Execute Query", test_execute_query),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    """Run the test suite."""
    success = run_all_tests()

    if success:
        print("\n✓ All tests passed! Database connection is working correctly.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        sys.exit(1)
