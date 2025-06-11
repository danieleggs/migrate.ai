#!/bin/bash

# Pre-sales Evaluator - Unified Application Startup Script
# This script starts the unified Pre-sales Evaluator application with both
# document evaluation and migration proposal generation capabilities.

echo "🚀 Starting Pre-sales Evaluator (Unified Application)..."
echo "=================================================="

# Check if .env file exists
if [ -f .env ]; then
    echo "✅ Found .env file"
    source .env
else
    echo "⚠️  No .env file found. Make sure OPENAI_API_KEY is set in your environment."
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY environment variable is not set!"
    echo "   Please set it with: export OPENAI_API_KEY='your-api-key-here'"
    exit 1
else
    echo "✅ OpenAI API key is configured"
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python -c "import streamlit, langchain, openai" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ All required packages are installed"
else
    echo "❌ Missing required packages. Installing..."
    pip install -r requirements.txt
fi

# Start the unified application
echo ""
echo "🌟 Features Available:"
echo "   • Document Evaluation (Migration Proposals & SOW Framework)"
echo "   • Migration Proposal Generation"
echo "   • Comprehensive Analysis & Recommendations"
echo ""
echo "🔗 Starting application on http://localhost:8501"
echo "   Press Ctrl+C to stop the application"
echo ""

streamlit run app.py 