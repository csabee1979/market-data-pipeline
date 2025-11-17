#!/bin/bash

# =============================================================================
# AI Research Papers Dashboard Launcher (Linux/Mac/WSL)
# =============================================================================
# 
# This script will:
# 1. Check if we're in the correct directory
# 2. Activate the virtual environment
# 3. Install/update dependencies if needed
# 4. Launch the Streamlit dashboard
# 
# Usage:
#   bash run_dashboard.sh
#   or
#   ./run_dashboard.sh (after making it executable: chmod +x run_dashboard.sh)
# 
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔬 AI Research Papers Dashboard${NC}"
    echo "=========================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ️  $1${NC}"
}

# Main function
main() {
    print_status
    
    # Check if we're in the correct directory (look for key files)
    if [[ ! -f "research_dashboard.py" || ! -f "dashboard_config.py" ]]; then
        print_error "Dashboard files not found in current directory!"
        print_info "Please run this script from the market-data-pipeline directory"
        print_info "Expected files: research_dashboard.py, dashboard_config.py"
        exit 1
    fi
    
    print_success "Found dashboard files"
    
    # Check for virtual environment
    if [[ ! -d ".venv" ]]; then
        print_warning "Virtual environment not found at .venv"
        print_info "Creating virtual environment..."
        python3 -m venv .venv
        if [[ $? -ne 0 ]]; then
            print_error "Failed to create virtual environment"
            exit 1
        fi
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source .venv/bin/activate
    
    if [[ $? -ne 0 ]]; then
        print_error "Failed to activate virtual environment"
        exit 1
    fi
    
    print_success "Virtual environment activated"
    
    # Check Python version
    python_version=$(python --version 2>&1)
    print_info "Using: $python_version"
    
    # Check if requirements.txt exists and install dependencies
    if [[ -f "requirements.txt" ]]; then
        print_info "Installing/updating dependencies from requirements.txt..."
        pip install -r requirements.txt --quiet
        
        if [[ $? -ne 0 ]]; then
            print_warning "Some dependencies may have failed to install"
            print_info "Continuing anyway..."
        else
            print_success "Dependencies installed successfully"
        fi
    else
        print_warning "requirements.txt not found, installing basic dependencies..."
        pip install streamlit plotly pandas psycopg2-binary python-dotenv --quiet
    fi
    
    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        print_warning ".env file not found!"
        print_info "Please create a .env file with your database credentials"
        print_info "You can copy from env.template if it exists"
        
        if [[ -f "env.template" ]]; then
            print_info "Found env.template - would you like to copy it to .env? (y/N)"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                cp env.template .env
                print_success "Copied env.template to .env"
                print_warning "Please edit .env file with your actual database credentials before continuing"
                print_info "Press Enter when ready to continue..."
                read -r
            fi
        fi
    fi
    
    # Test database connection (optional)
    if [[ -f "database/database.py" ]]; then
        print_info "Testing database connection..."
        python -c "
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
"
    fi
    
    # Launch dashboard
    echo ""
    print_info "Launching Streamlit dashboard..."
    print_info "The dashboard will open in your web browser at http://localhost:8501"
    print_info "Press Ctrl+C to stop the dashboard server"
    echo ""
    
    # Check if we should use the Python launcher or direct streamlit
    if [[ -f "run_dashboard.py" ]]; then
        print_info "Using Python launcher script..."
        python run_dashboard.py
    else
        print_info "Launching directly with streamlit..."
        streamlit run research_dashboard.py
    fi
    
    # Cleanup message
    echo ""
    print_info "Dashboard stopped. Virtual environment is still active."
    print_info "Run 'deactivate' to exit the virtual environment"
}

# Error handling
set -e
trap 'print_error "Script failed on line $LINENO"' ERR

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    print_error "Python not found! Please install Python 3.7+ first."
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    alias python=python3
fi

# Run main function
main "$@"
