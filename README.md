# migrate.ai Pre-Sales Evaluator

A comprehensive document evaluation system designed to assess migration proposals and statements of work against migrate.ai's Agent-Led Migration Specification. Built with LangGraph orchestration and Streamlit interface.

## Features

- **Migration Proposal Analysis**: Evaluate proposals against migrate.ai Agent-Led Migration Specification
- **Statement of Work Evaluation**: Framework for SOW assessment (implementation in progress)
- **Migration Proposal Generator**: Generate comprehensive migration proposals from discovery data
- **Multi-Agent Architecture**: LangGraph-orchestrated evaluation workflow
- **Interactive Interface**: Streamlit-based web application
- **Comprehensive Reporting**: Detailed analysis with scoring, gaps, and recommendations

## Architecture

The system uses a multi-agent architecture orchestrated by LangGraph:

### Core Agents

1. **Document Parser**: Extract and structure content from uploaded documents
2. **Phase Evaluators**: Assess each migration phase (Strategise & Plan, Migrate & Modernise, Manage & Optimise)
3. **Gap Highlighter**: Identify weaknesses and missing elements
4. **Recommendations Generator**: Provide actionable improvement suggestions
5. **Spec Checker**: Validate against migrate.ai specification
6. **Scoring Agent**: Calculate final evaluation scores

### Workflow

```
Document Upload → Parse Content → Phase Evaluation → Gap Analysis → 
Recommendations → Spec Compliance → Final Scoring → Report Generation
```

## Installation

### Prerequisites

- Python 3.9+
- OpenAI API key

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pre-sales-evaluator
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Usage

### Migration Proposal Evaluation

1. **Upload Document**: Support for PDF, DOCX, TXT, and MD files
2. **Select Evaluation Type**: Choose "Migration Proposal Evaluation"
3. **Configure Options**: Select display preferences for detailed analysis
4. **Review Results**: Comprehensive evaluation with:
   - Phase-by-phase scoring (0-3 scale)
   - Specification compliance analysis
   - Gap identification and prioritisation
   - Actionable recommendations
   - Final score (0-100) with grade

### Statement of Work Evaluation

Framework for SOW assessment focusing on:
- Scope definition and clarity
- Deliverables specification
- Timeline and milestones
- Resource allocation
- Risk and assumption management

### Migration Proposal Generator

Generate comprehensive migration proposals from discovery data:
- Application portfolio analysis
- Migration wave planning
- Technology stack evaluation
- Risk assessment and mitigation
- Resource and timeline estimation

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Evaluation Criteria

The system evaluates proposals against migrate.ai specification:

#### Core Principles
- GenAI and agents used across the lifecycle
- Minimum viable refactor preferred over full rewrites
- Platform-neutral tooling and artefacts
- Reusable components and fallback paths
- Client self-sufficiency via internal tooling
- Alignment with AWS MAP and Azure Migration Program

#### Migration Phases
1. **Strategise and Plan**: Assessment, strategy, and planning
2. **Migrate and Modernise**: Execution with dual-track agile delivery
3. **Manage and Optimise**: Operations and continuous improvement

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Production Deployment

#### AWS ECS Fargate
See `deploy/aws.md` for detailed ECS deployment instructions.

#### Azure Container Instances
See `deploy/azure.md` for Azure deployment guide.

#### Docker
```bash
docker build -t migrate-ai-evaluator .
docker run -p 8501:8501 -e OPENAI_API_KEY=your_key migrate-ai-evaluator
```

## Project Structure

```
├── app.py                          # Main Streamlit application
├── src/
│   ├── agents/                     # LangGraph agent implementations
│   │   ├── phase_evaluator.py      # Phase evaluation agents
│   │   ├── gap_highlighter.py      # Gap analysis agent
│   │   ├── recommendations_generator.py # Recommendations agent
│   │   ├── spec_checker.py         # Specification compliance agent
│   │   └── scoring_node.py         # Final scoring agent
│   ├── models/                     # Data models and types
│   │   ├── evaluation.py           # Evaluation data structures
│   │   └── evaluation_types.py     # Evaluation type configurations
│   ├── utils/                      # Utility functions
│   │   ├── document_parser.py      # Document parsing utilities
│   │   └── json_parser.py          # JSON response parsing
│   ├── workflows/                  # LangGraph workflow definitions
│   │   └── evaluation_workflow.py  # Main evaluation workflow
│   └── config/                     # Configuration files
│       └── modernize_ai_spec.yaml  # Migration evaluation criteria
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
└── README.md                       # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Licence

This project is proprietary software developed for migrate.ai evaluation purposes.

## Support

For support and questions, please contact the development team. 