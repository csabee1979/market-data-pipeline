"""
Database utility module for connecting to Neon PostgreSQL database.

This module provides functions to:
- Load database credentials from .env file
- Build connection string
- Connect to the database
- Verify database connection
- Execute queries with proper error handling
"""

import os
import sys
from typing import Optional, Tuple
from contextlib import contextmanager

import psycopg2
from psycopg2 import Error as PostgresError
from psycopg2.extensions import connection as PostgresConnection
from dotenv import load_dotenv


class DatabaseConfig:
    """Configuration class for database connection parameters."""

    def __init__(self):
        """Initialize database configuration from Streamlit secrets or environment variables."""
        # Load environment variables from .env file
        load_dotenv()

        # Try Streamlit secrets first (for cloud deployment), then fall back to environment variables
        try:
            import streamlit as st

            if hasattr(st, "secrets") and st.secrets:
                # Use Streamlit secrets (flat format, no section)
                self.host = st.secrets.get("DB_HOST")
                self.database = st.secrets.get("DB_NAME")
                self.user = st.secrets.get("DB_USER")
                self.password = st.secrets.get("DB_PASSWORD")
                self.sslmode = st.secrets.get("DB_SSLMODE", "require")

                # Only use secrets if all required values are present
                if all([self.host, self.database, self.user, self.password]):
                    # Debug info for cloud deployment
                    print(
                        f"🔐 Using Streamlit secrets: host={self.host[:20]}..., db={self.database}, user={self.user}"
                    )
                    return
        except (ImportError, KeyError, AttributeError) as e:
            print(f"⚠️ Streamlit secrets failed: {e}")
            pass

        # Fall back to environment variables (.env file)
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.sslmode = os.getenv("DB_SSLMODE", "require")

        print(
            f"🌍 Using environment variables: host={self.host[:20] if self.host else 'None'}..., db={self.database}, user={self.user}"
        )

        # Validate that all required parameters are loaded
        missing_params = []
        if not self.host:
            missing_params.append("DB_HOST")
        if not self.database:
            missing_params.append("DB_NAME")
        if not self.user:
            missing_params.append("DB_USER")
        if not self.password:
            missing_params.append("DB_PASSWORD")

        if missing_params:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_params)}. "
                "Please create a .env file with all required database parameters. "
                "See env.template for an example."
            )

    def get_connection_string(self) -> str:
        """
        Build PostgreSQL connection string.

        Returns:
            str: PostgreSQL connection string with all parameters
        """
        return (
            f"postgresql://{self.user}:{self.password}@{self.host}/{self.database}"
            f"?sslmode={self.sslmode}"
        )

    def get_connection_params(self) -> dict:
        """
        Get connection parameters as a dictionary.

        Returns:
            dict: Dictionary with connection parameters for psycopg2
        """
        return {
            "host": self.host,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "sslmode": self.sslmode,
        }


class DatabaseConnection:
    """Database connection manager with context manager support."""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database connection manager.

        Args:
            config: DatabaseConfig instance. If None, creates a new one.
        """
        self.config = config or DatabaseConfig()
        self.connection: Optional[PostgresConnection] = None

    def connect(self) -> PostgresConnection:
        """
        Establish connection to the database.

        Returns:
            PostgresConnection: Active database connection

        Raises:
            PostgresError: If connection fails
        """
        try:
            self.connection = psycopg2.connect(**self.config.get_connection_params())
            return self.connection
        except PostgresError as e:
            raise PostgresError(f"Failed to connect to database: {e}") from e

    def disconnect(self):
        """Close the database connection if it exists."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None

    def __enter__(self) -> PostgresConnection:
        """Context manager entry - establish connection."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.disconnect()


def verify_connection() -> Tuple[bool, str]:
    """
    Verify database connection by connecting and running a simple query.

    Returns:
        Tuple[bool, str]: (success, message) tuple
            - success: True if connection successful, False otherwise
            - message: Success or error message
    """
    try:
        # Create database configuration
        config = DatabaseConfig()

        # Try to connect
        with DatabaseConnection(config) as conn:
            # Create a cursor
            with conn.cursor() as cursor:
                # Run a simple test query
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]

                # Get current database name
                cursor.execute("SELECT current_database();")
                db_name = cursor.fetchone()[0]

                # Get current user
                cursor.execute("SELECT current_user;")
                user = cursor.fetchone()[0]

                success_msg = (
                    f"✓ Successfully connected to database!\n"
                    f"  Database: {db_name}\n"
                    f"  User: {user}\n"
                    f"  PostgreSQL version: {version[:50]}..."
                )

                return True, success_msg

    except ValueError as e:
        # Configuration error (missing .env or DB_PASSWORD)
        return False, f"✗ Configuration error: {e}"

    except PostgresError as e:
        # Database connection error
        return False, f"✗ Database connection error: {e}"

    except Exception as e:  # pylint: disable=broad-except
        # Unexpected error - we want to catch everything here for user-friendly error reporting
        return False, f"✗ Unexpected error: {e}"


@contextmanager
def get_connection():
    """
    Context manager for database connections.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
            results = cursor.fetchall()

    Yields:
        PostgresConnection: Active database connection
    """
    db = DatabaseConnection()
    try:
        conn = db.connect()
        yield conn
    finally:
        db.disconnect()


def execute_query(query: str, params: Optional[tuple] = None, fetch: bool = True):
    """
    Execute a SQL query with proper error handling.

    Args:
        query: SQL query string
        params: Query parameters (optional)
        fetch: Whether to fetch results (default: True)

    Returns:
        Query results if fetch=True, None otherwise

    Raises:
        PostgresError: If query execution fails
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)

                if fetch:
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return None

    except PostgresError as e:
        raise PostgresError(f"Query execution failed: {e}") from e


if __name__ == "__main__":
    """Test the database connection when run as a script."""
    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print("Testing database connection...")
    print("-" * 60)

    success, message = verify_connection()
    print(message)

    if success:
        print("-" * 60)
        print("\n✓ Database module is working correctly!")
        sys.exit(0)
    else:
        print("-" * 60)
        print("\n✗ Database connection failed. Please check your configuration.")
        sys.exit(1)
