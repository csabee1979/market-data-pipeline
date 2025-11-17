# =============================================================================
# AI Research Papers Dashboard Launcher (PowerShell)
# =============================================================================
# 
# This PowerShell script will:
# 1. Check if we're in the correct directory
# 2. Activate the virtual environment
# 3. Install/update dependencies if needed
# 4. Launch the Streamlit dashboard
# 
# Usage:
#   .\run_dashboard.ps1
#   or
#   powershell -ExecutionPolicy Bypass -File run_dashboard.ps1
# 
# Note: You may need to set execution policy:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# 
# =============================================================================

# Function to print colored output
function Write-Status {
    Write-Host "🔬 AI Research Papers Dashboard" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
}

function Write-Success {
    param($Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param($Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

# Main function
function Main {
    Write-Status
    
    # Check if we're in the correct directory (look for key files)
    if (!(Test-Path "dashboard_app\research_dashboard.py") -or !(Test-Path "dashboard_app\dashboard_config.py")) {
        Write-Error "Dashboard files not found in current directory!"
        Write-Info "Please run this script from the market-data-pipeline directory"
        Write-Info "Expected files: dashboard_app\research_dashboard.py, dashboard_app\dashboard_config.py"
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Success "Found dashboard files"
    
    # Check for virtual environment
    if (!(Test-Path ".venv")) {
        Write-Warning "Virtual environment not found at .venv"
        Write-Info "Creating virtual environment..."
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create virtual environment"
            Write-Info "Make sure Python 3.7+ is installed and in PATH"
            Read-Host "Press Enter to exit"
            exit 1
        }
        Write-Success "Virtual environment created"
    }
    
    # Activate virtual environment
    Write-Info "Activating virtual environment..."
    
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .venv\Scripts\Activate.ps1
    } elseif (Test-Path ".venv\Scripts\activate.bat") {
        cmd /c ".venv\Scripts\activate.bat"
    } else {
        Write-Error "Could not find virtual environment activation script"
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Success "Virtual environment activated"
    
    # Check Python version
    $pythonVersion = & python --version 2>&1
    Write-Info "Using: $pythonVersion"
    
    # Check if requirements.txt exists and install dependencies
    if (Test-Path "requirements.txt") {
        Write-Info "Installing/updating dependencies from requirements.txt..."
        & pip install -r requirements.txt --quiet
        
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Some dependencies may have failed to install"
            Write-Info "Continuing anyway..."
        } else {
            Write-Success "Dependencies installed successfully"
        }
    } else {
        Write-Warning "requirements.txt not found, installing basic dependencies..."
        & pip install streamlit plotly pandas psycopg2-binary python-dotenv --quiet
    }
    
    # Check if .env file exists
    if (!(Test-Path ".env")) {
        Write-Warning ".env file not found!"
        Write-Info "Please create a .env file with your database credentials"
        
        if (Test-Path "env.template") {
            $response = Read-Host "Found env.template - would you like to copy it to .env? (y/N)"
            if ($response -eq "y" -or $response -eq "Y") {
                Copy-Item "env.template" ".env"
                Write-Success "Copied env.template to .env"
                Write-Warning "Please edit .env file with your actual database credentials before continuing"
                Read-Host "Press Enter when ready to continue"
            }
        }
    }
    
    # Test database connection (optional)
    if (Test-Path "database\database.py") {
        Write-Info "Testing database connection..."
        try {
            $testResult = & python -c @"
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath('.')), 'database'))
try:
    from database import verify_connection
    success, message = verify_connection()
    if success:
        print('✅ Database connection successful')
    else:
        print(f'⚠️  Database connection warning: {message}')
except Exception as e:
    print(f'⚠️  Could not test database connection: {e}')
"@
            Write-Host $testResult
        } catch {
            Write-Warning "Could not test database connection"
        }
    }
    
    # Launch dashboard
    Write-Host ""
    Write-Info "Launching Streamlit dashboard..."
    Write-Info "The dashboard will open in your web browser at http://localhost:8501"
    Write-Info "Press Ctrl+C to stop the dashboard server"
    Write-Host ""
    
    # Check if we should use the Python launcher or direct streamlit
    if (Test-Path "run_dashboard.py") {
        Write-Info "Using Python launcher script..."
        & python run_dashboard.py
    } else {
        Write-Info "Launching directly with streamlit..."
        & streamlit run dashboard_app\research_dashboard.py
    }
    
    # Cleanup message
    Write-Host ""
    Write-Info "Dashboard stopped. Virtual environment is still active."
    Write-Info "You can close this window or run 'deactivate' to exit the virtual environment"
    Read-Host "Press Enter to exit"
}

# Error handling
$ErrorActionPreference = "Stop"

# Check if Python is available
try {
    $null = & python --version 2>&1
} catch {
    try {
        $null = & python3 --version 2>&1
        Set-Alias python python3
    } catch {
        Write-Error "Python not found! Please install Python 3.7+ first."
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Run main function
try {
    Main
} catch {
    Write-Error "Script failed: $($_.Exception.Message)"
    Read-Host "Press Enter to exit"
    exit 1
}
