@echo off
setlocal enabledelayedexpansion
REM =============================================================================
REM AI Research Papers Dashboard Launcher (Windows)
REM =============================================================================
REM 
REM This batch script will:
REM 1. Check if we're in the correct directory
REM 2. Activate the virtual environment
REM 3. Install/update dependencies if needed
REM 4. Launch the Streamlit dashboard
REM 
REM Usage:
REM   run_dashboard.bat
REM   or
REM   Double-click the file in Windows Explorer
REM 
REM =============================================================================

echo 🔬 AI Research Papers Dashboard
echo ==========================================

REM Check if we're in the correct directory (look for key files)
if not exist "dashboard_app\research_dashboard.py" (
    echo ❌ dashboard_app\research_dashboard.py not found!
    echo ℹ️  Please run this script from the market-data-pipeline directory
    pause
    exit /b 1
)

if not exist "dashboard_app\dashboard_config.py" (
    echo ❌ dashboard_app\dashboard_config.py not found!
    echo ℹ️  Please run this script from the market-data-pipeline directory
    pause
    exit /b 1
)

echo ✅ Found dashboard files

REM Check for virtual environment
if not exist ".venv" (
    echo ⚠️  Virtual environment not found at .venv
    echo ℹ️  Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        echo ℹ️  Make sure Python 3.7+ is installed and in PATH
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo ℹ️  Activating virtual environment...
call .venv\Scripts\activate

if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated

REM Check Python version
echo ℹ️  Using Python version:
python --version

REM Check if requirements.txt exists and install dependencies
if exist "requirements.txt" (
    echo ℹ️  Installing/updating dependencies from requirements.txt...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo ⚠️  Some dependencies may have failed to install
        echo ℹ️  Continuing anyway...
    ) else (
        echo ✅ Dependencies installed successfully
    )
) else (
    echo ⚠️  requirements.txt not found, installing basic dependencies...
    pip install streamlit plotly pandas psycopg2-binary python-dotenv --quiet
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  .env file not found!
    echo ℹ️  Please create a .env file with your database credentials
    
    if exist "env.template" (
        echo ℹ️  Found env.template - would you like to copy it to .env? (y/N)
        set /p response="Enter choice: "
        if /i "!response!"=="y" (
            copy env.template .env > nul
            echo ✅ Copied env.template to .env
            echo ⚠️  Please edit .env file with your actual database credentials before continuing
            echo ℹ️  Press Enter when ready to continue...
            pause > nul
        )
    )
)

REM Test database connection (optional)
if exist "database\database.py" (
    echo ℹ️  Testing database connection...
    python -c "import sys, os; sys.path.insert(0, 'database'); from database import verify_connection; s, m = verify_connection(); print('✅ Database connection successful' if s else '⚠️  Database connection warning:', m)" 2>nul || echo ⚠️  Could not test database connection
)

REM Launch dashboard
echo.
echo ℹ️  Launching Streamlit dashboard...
echo ℹ️  The dashboard will open in your web browser at http://localhost:8501
echo ℹ️  Press Ctrl+C to stop the dashboard server
echo.

REM Check if we should use the Python launcher or direct streamlit
if exist "run_dashboard.py" (
    echo ℹ️  Using Python launcher script...
    python run_dashboard.py
) else (
    echo ℹ️  Launching directly with streamlit...
    streamlit run dashboard_app\research_dashboard.py
)

REM Cleanup message
echo.
echo ℹ️  Dashboard stopped. You can close this window or run the script again.
pause
