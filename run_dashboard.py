#!/usr/bin/env python3
"""
Dashboard Launcher Script

Simple script to launch the Streamlit dashboard with proper environment setup
and error checking.

Usage:
    python run_dashboard.py

This script will:
1. Check if virtual environment is activated
2. Verify database connection
3. Launch the Streamlit dashboard
4. Handle common startup errors
"""

import os
import sys
import subprocess
from pathlib import Path


def check_virtual_env():
    """Check if virtual environment is activated."""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def check_dependencies():
    """Check if required packages are installed."""
    required_packages = ["streamlit", "plotly", "pandas", "psycopg2"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    return missing_packages


def check_database_connection():
    """Check if database connection is working."""
    try:
        # Import database module
        sys.path.insert(
            0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
        )
        from database import verify_connection

        success, message = verify_connection()
        return success, message
    except Exception as e:
        return False, f"Database connection check failed: {e}"


def main():
    """Main launcher function."""
    print("🚀 AI Research Papers Dashboard Launcher")
    print("=" * 50)

    # Check virtual environment
    if not check_virtual_env():
        print("⚠️  Warning: Virtual environment not detected.")
        print("   Consider activating .venv before running the dashboard.")
        print("   Windows: .venv\\Scripts\\activate")
        print("   Linux/Mac: source .venv/bin/activate")
        print()

    # Check dependencies
    print("📦 Checking dependencies...")
    missing_packages = check_dependencies()

    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("   Please install them with: pip install -r requirements.txt")
        return 1
    else:
        print("✅ All dependencies found")

    # Check database connection
    print("🔌 Checking database connection...")
    db_success, db_message = check_database_connection()

    if not db_success:
        print(f"❌ Database connection failed: {db_message}")
        print("   Please check your .env file and database credentials.")
        return 1
    else:
        print("✅ Database connection successful")

    # Launch dashboard
    print("🎯 Launching Streamlit dashboard...")
    print("   The dashboard will open in your web browser at http://localhost:8501")
    print("   Press Ctrl+C to stop the dashboard server")
    print()

    try:
        # Launch Streamlit
        dashboard_file = (
            Path(__file__).parent / "dashboard_app" / "research_dashboard.py"
        )

        if not dashboard_file.exists():
            print(f"❌ Dashboard file not found: {dashboard_file}")
            return 1

        # Run streamlit
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(dashboard_file)], check=False
        )

        return result.returncode

    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
