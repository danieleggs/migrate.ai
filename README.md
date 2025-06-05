# Pre-sales Evaluator

An AI-powered document evaluation system that intelligently analyzes migration proposals against the Modernize.AI specification.

## 🚀 Features

- **Intelligent Document Parsing**: Supports PDF, DOCX, and text files
- **Smart Phase Routing**: Only evaluates relevant migration phases based on content
- **Comprehensive Analysis**: Spec compliance, gap analysis, and recommendations
- **Modern UI**: Clean Streamlit interface with real-time progress tracking
- **Robust Error Handling**: Graceful fallbacks for LLM parsing issues

## 🏗️ Architecture

- **LangGraph**: Orchestrates the evaluation workflow
- **OpenAI GPT-4o-mini**: Fast, cost-effective LLM for analysis
- **Streamlit**: Web interface
- **Pydantic**: Data validation and modeling

## 🔧 Local Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pre-sales-evaluator
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## ☁️ Cloud Deployment Options

### 1. Streamlit Cloud (Recommended - Free)
- **Pros**: Free, automatic deployments, built-in secrets management
- **Setup**: 5 minutes
- **Instructions**: See `deploy/streamlit_cloud.md`

### 2. Heroku
- **Pros**: Easy deployment, custom domains, add-ons
- **Setup**: 10 minutes
- **Instructions**: See `deploy/heroku.md`

### 3. AWS App Runner
- **Pros**: Highly scalable, enterprise-grade, auto-scaling
- **Setup**: 20 minutes
- **Instructions**: See `deploy/aws.md`

### 4. Docker (Any Platform)
```bash
# Build and run locally
docker build -t pre-sales-evaluator .
docker run -p 8501:8501 -e OPENAI_API_KEY="your-key" pre-sales-evaluator

# Or use docker-compose
docker-compose up
```

## 📊 Usage

1. **Upload Document**: Drag and drop your migration proposal
2. **Wait for Analysis**: The system intelligently routes to relevant phases
3. **Review Results**: Get comprehensive evaluation with scores and recommendations

## 🔒 Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## 📁 Project Structure

```
├── app.py                          # Streamlit web interface
├── src/
│   ├── agents/                     # LLM agents for different tasks
│   ├── graph/                      # LangGraph workflow orchestration
│   ├── models/                     # Pydantic data models
│   ├── utils/                      # Utility functions
│   └── config/                     # Configuration files
├── deploy/                         # Deployment instructions
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
└── docker-compose.yml             # Local container orchestration
```

## 🎯 Performance Optimizations

- **Smart Routing**: Only evaluates relevant phases (saves ~50% processing time)
- **Content Limiting**: Processes 2000 chars for faster analysis
- **Rate Limiting**: Built-in delays to avoid API limits
- **Robust Parsing**: Fallback mechanisms for reliable operation

## 🔧 Troubleshooting

### Rate Limiting
If you hit OpenAI rate limits, the system includes automatic delays and will retry.

### Document Parsing Issues
The system supports multiple document formats and includes debugging output.

### API Key Issues
Ensure your OpenAI API key is set correctly and has sufficient credits.

## 📈 Monitoring

- **Streamlit Health Check**: Built-in health monitoring
- **Debug Output**: Comprehensive logging for troubleshooting
- **Error Handling**: Graceful degradation with meaningful error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 