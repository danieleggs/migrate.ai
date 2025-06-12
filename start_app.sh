#!/bin/bash

# Pre-Sales Document Evaluator Startup Script
# Comprehensive migration proposal evaluation system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print banner
echo -e "${BLUE}"
echo "=================================================="
echo "  migrate.ai Pre-Sales Document Evaluator"
echo "=================================================="
echo -e "${NC}"

print_status "Starting migrate.ai Pre-Sales Document Evaluator..."
echo ""
echo "Features:"
echo "- Document Evaluation: Evaluate proposals against migrate.ai specification"
echo "- SOW Framework: Assess Statement of Work documents"
echo "- Migration Proposal Generator: Generate comprehensive migration proposals"
echo "- Multi-Agent Architecture: LangGraph-orchestrated evaluation workflow"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_status "Please edit .env file and add your OpenAI API key"
        print_warning "Application will not work without OPENAI_API_KEY"
    else
        print_error ".env.example not found. Please create .env file manually"
        exit 1
    fi
fi

# Check if OpenAI API key is set
if [ -f .env ]; then
    source .env
    if [ -z "$OPENAI_API_KEY" ]; then
        print_error "OPENAI_API_KEY not set in .env file"
        print_status "Please add your OpenAI API key to .env file:"
        print_status "OPENAI_API_KEY=your_api_key_here"
        exit 1
    fi
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.9+ required. Current version: $python_version"
    exit 1
fi

print_success "Python version check passed: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
print_status "Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependencies installed"

# Check if required directories exist
required_dirs=("src/config" "src/agents" "src/models" "src/utils")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        print_error "Required directory missing: $dir"
        exit 1
    fi
done

print_success "Directory structure validated"

# Check if required config files exist
if [ ! -f "src/config/modernize_ai_spec.yaml" ]; then
    print_error "migrate.ai specification file missing: src/config/modernize_ai_spec.yaml"
    exit 1
fi

print_success "Configuration files validated"

# Set default port if not specified
PORT=${STREAMLIT_SERVER_PORT:-8501}
ADDRESS=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}

print_status "Starting Streamlit application..."
print_status "Server will be available at: http://localhost:$PORT"
print_status "Press Ctrl+C to stop the server"
echo ""

# Start the application
exec streamlit run app.py \
    --server.port=$PORT \
    --server.address=$ADDRESS \
    --server.headless=true \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false 