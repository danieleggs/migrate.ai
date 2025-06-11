# Pre-sales Evaluator

An AI-powered document evaluation and migration proposal generation system that provides comprehensive analysis and planning for cloud migration projects.

## 🚀 Features

### Document Evaluation
- **Intelligent Document Parsing**: Supports PDF, DOCX, and text files
- **Smart Phase Routing**: Only evaluates relevant migration phases based on content
- **Comprehensive Analysis**: Spec compliance, gap analysis, and recommendations
- **Multiple Evaluation Types**: Migration Proposals and SOW Framework evaluation

### Migration Proposal Generation
- **Discovery Data Processing**: Analyze and classify applications from discovery inputs
- **6R Strategy Classification**: Intelligent migration strategy recommendations
- **Wave Planning**: Dual-track methodology for migration sequencing
- **Architecture Recommendations**: Cloud-native architecture guidance
- **GenAI Tool Planning**: AI-powered automation opportunities
- **Effort Estimation**: Sprint-based project planning

### Modern Interface
- **Clean Streamlit UI**: Intuitive web interface with real-time progress tracking
- **Multiple Export Formats**: Markdown, YAML, and JSON outputs
- **Comprehensive Visualizations**: Charts and graphs for analysis results
- **Robust Error Handling**: Graceful fallbacks for LLM parsing issues

## 🏗️ Architecture

- **LangGraph**: Orchestrates both evaluation and generation workflows
- **OpenAI GPT-4o-mini**: Fast, cost-effective LLM for analysis
- **Streamlit**: Web interface with multi-page navigation
- **Pydantic**: Data validation and modeling
- **Separated Agent Architecture**: Individual agents for maintainability

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

### 1. AWS App Runner (Recommended)
- **Pros**: Highly scalable, enterprise-grade, auto-scaling
- **Setup**: 20 minutes
- **Instructions**: See `deploy/aws.md`

### 2. Azure Container Apps
- **Pros**: Easy deployment, custom domains, enterprise integration
- **Setup**: 15 minutes
- **Instructions**: See `deploy/azure.md`

### 3. Docker (Any Platform)
```bash
# Build and run locally
docker build -t pre-sales-evaluator .
docker run -p 8501:8501 -e OPENAI_API_KEY="your-key" pre-sales-evaluator

# Or use docker-compose
docker-compose up
```

## 📊 Usage

### Document Evaluation
1. **Select Evaluation Type**: Choose "Migration Proposals" or "SOW Framework"
2. **Upload Document**: Drag and drop your document
3. **Wait for Analysis**: The system intelligently routes to relevant phases
4. **Review Results**: Get comprehensive evaluation with scores and recommendations

### Migration Proposal Generation
1. **Select "Migration Proposal Generator"**
2. **Input Discovery Data**: Provide application and infrastructure details
3. **Configure Parameters**: Set client information and project context
4. **Generate Proposal**: AI creates comprehensive migration proposal
5. **Export Results**: Download in multiple formats

## 🔒 Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## 📁 Project Structure

```
├── app.py                          # Unified Streamlit web interface
├── src/
│   ├── agents/                     # Individual LLM agents
│   │   ├── parse_discovery_input.py
│   │   ├── workload_classifier.py
│   │   ├── wave_planner.py
│   │   ├── migration_strategist.py
│   │   ├── content_generator.py
│   │   ├── proposal_formatter.py
│   │   └── proposal_nodes.py       # Remaining agents
│   ├── graph/                      # LangGraph workflow orchestration
│   │   ├── evaluation_graph.py    # Document evaluation workflow
│   │   └── proposal_generation_graph.py # Proposal generation workflow
│   ├── models/                     # Pydantic data models
│   ├── utils/                      # Utility functions
│   └── config/                     # Configuration files
├── deploy/                         # Deployment instructions
├── tests/                          # Test suite
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
└── docker-compose.yml             # Local container orchestration
```

## 🎯 Performance Optimizations

- **Smart Routing**: Only evaluates relevant phases (saves ~50% processing time)
- **Separated Agents**: Individual agents for better maintainability and testing
- **Content Limiting**: Processes optimal content chunks for faster analysis
- **Rate Limiting**: Built-in delays to avoid API limits
- **Robust Parsing**: Fallback mechanisms for reliable operation
- **Lazy LLM Initialization**: API keys loaded when needed

## 🔧 Troubleshooting

### Rate Limiting
If you hit OpenAI rate limits, the system includes automatic delays and will retry.

### Document Parsing Issues
The system supports multiple document formats and includes debugging output.

### API Key Issues
Ensure your OpenAI API key is set correctly and has sufficient credits. The system uses lazy initialization to load API keys when needed.

### Agent Architecture
Each agent is separated into individual files for better maintainability. If you encounter import issues, check the agent function names in `src/agents/__init__.py`.

## 📈 Monitoring

- **Streamlit Health Check**: Built-in health monitoring
- **Debug Output**: Comprehensive logging for troubleshooting
- **Error Handling**: Graceful degradation with meaningful error messages
- **Progress Tracking**: Real-time progress indicators for long-running operations

## 🧪 Testing

Run the test suite to ensure everything is working correctly:

```bash
pytest tests/ -v
```

The test suite covers:
- Model validation and creation
- Utility functions
- Document parsing
- Type detection
- Agent functionality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 