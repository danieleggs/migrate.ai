# LangGraph Workflow Documentation

## Overview

The migrate.ai Pre-Sales Evaluator uses LangGraph to orchestrate a sophisticated multi-agent workflow for document evaluation and migration proposal generation. This document outlines the workflow architecture, agent interactions, and data flow.

## Architecture

### Core Components

1. **Document Parser**: Extracts and structures content from uploaded documents
2. **Phase Evaluators**: Assess each migration phase against specification
3. **Spec Checker**: Validates overall compliance with migrate.ai specification
4. **Gap Highlighter**: Identifies weaknesses and missing elements
5. **Recommendations Generator**: Provides actionable improvement suggestions
6. **Scoring Agent**: Calculates final evaluation scores

### Workflow Types

#### 1. Migration Proposal Evaluation

**Purpose**: Comprehensive evaluation of migration proposals against migrate.ai Agent-Led Migration Specification

**Flow**:
```
Document Upload → Parse Content → Phase Evaluation → Spec Compliance → 
Gap Analysis → Recommendations → Final Scoring → Report Generation
```

**Key Features**:
- **Purpose**: Validates compliance against migrate.ai specification
- **Phases**: Strategise & Plan, Migrate & Modernise, Manage & Optimise
- **Scoring**: 0-3 scale per phase, 0-100 overall score
- **Reference**: `src/config/modernize_ai_spec.yaml`

#### 2. Statement of Work Evaluation

**Purpose**: Framework for evaluating SOW documents for completeness and quality

**Flow**:
```
Document Upload → Parse Content → Scope Analysis → Dependencies Review → 
Assumptions Validation → Risk Assessment → Deliverables Check → Report Generation
```

**Key Features**:
- Scope definition and clarity assessment
- Deliverables specification validation
- Timeline and milestone evaluation
- Resource allocation analysis

#### 3. Migration Proposal Generator

**Purpose**: Generate comprehensive migration proposals from discovery data

**Flow**:
```
Discovery Data → Parse Input → Application Classification → Wave Planning → 
Strategy Assignment → Architecture Recommendations → Effort Estimation → Proposal Generation
```

**Key Features**:
- Application portfolio analysis
- Migration wave planning with dual-track agile delivery methodology
- 6R strategy classification with modernisation bias
- GenAI tool integration planning

## Agent Specifications

### Document Parser
- **Input**: Raw document content (PDF, DOCX, TXT, MD)
- **Output**: Structured content with metadata
- **Function**: Content extraction and normalisation

### Phase Evaluators
- **Input**: Document content, phase specification
- **Output**: Phase evaluation with score, strengths, weaknesses
- **Function**: Assess specific migration phases

### Spec Checker
- **Input**: Document content, core principles, red flags
- **Output**: Compliance score and analysis
- **Function**: Overall specification compliance validation

### Gap Highlighter
- **Input**: Phase evaluations, spec compliance results
- **Output**: Categorised gaps by priority
- **Function**: Identify weaknesses and missing elements

### Recommendations Generator
- **Input**: Gap analysis, evaluation results
- **Output**: Prioritised actionable recommendations
- **Function**: Generate improvement suggestions

### Scoring Agent
- **Input**: All evaluation components
- **Output**: Final score with breakdown and grade
- **Function**: Calculate comprehensive evaluation score

## Data Models

### Core Evaluation Types
```python
class MigrationPhase(Enum):
    STRATEGISE_AND_PLAN = "strategise_and_plan"
    MIGRATE_AND_MODERNISE = "migrate_and_modernise"
    MANAGE_AND_OPTIMISE = "manage_and_optimise"

class PhaseEvaluation(BaseModel):
    phase: MigrationPhase
    score: int  # 0-3 scale
    strengths: List[str]
    weaknesses: List[str]
    evidence: List[str]
    recommendations: List[str]

class SpecCompliance(BaseModel):
    overall_compliance_score: float  # 0.0-1.0
    missing_elements: List[str]
    compliance_strengths: List[str]
    improvement_areas: List[str]
    recommendations: List[str]
```

### Gap Analysis
```python
class GapAnalysis(BaseModel):
    critical_gaps: List[Dict[str, str]]
    high_priority_gaps: List[Dict[str, str]]
    medium_priority_gaps: List[Dict[str, str]]
    low_priority_gaps: List[Dict[str, str]]
```

### Final Results
```python
class FinalScore(BaseModel):
    final_score: int  # 0-100 scale
    score_breakdown: Dict[str, Any]
    score_rationale: str
    grade: str  # A, B, C, D, F

class EvaluationResult(BaseModel):
    phase_evaluations: List[PhaseEvaluation]
    spec_compliance: Optional[SpecCompliance]
    gap_analysis: Optional[GapAnalysis]
    recommendations: Optional[Recommendations]
    final_score: Optional[FinalScore]
    errors: List[str]
```

## Configuration

### Specification Files
- **Migration Spec**: `src/config/modernize_ai_spec.yaml`
- **SOW Spec**: `src/config/sow_spec.yaml` (planned)

### Model Configuration
- **Primary Model**: GPT-4o-mini
- **Temperature**: 0 (deterministic results)
- **Timeout**: 30 seconds per API call

### Evaluation Criteria

#### Core Principles (migrate.ai)
- GenAI and agents used across the lifecycle
- Minimum viable refactor preferred over full rewrites
- Platform-neutral tooling and artefacts
- Reusable components and fallback paths
- Client self-sufficiency via internal tooling
- Alignment with AWS MAP and Azure Migration Program

#### Red Flags
- Big-bang migration approach without phased delivery
- Lack of automation and manual-heavy processes
- No GenAI or AI-assisted tooling mentioned
- Platform-specific solutions without portability
- Missing fallback and rollback strategies

## Error Handling

### Graceful Degradation
- Individual agent failures don't stop the entire workflow
- Fallback responses for parsing errors
- Comprehensive error logging and reporting

### Validation
- Input validation at each stage
- Content format verification
- API response validation with fallbacks

## Performance Optimisations

### Caching
- Result caching to avoid redundant processing
- Content hashing for change detection
- Session persistence across UI interactions

### Parallel Processing
- Phase evaluators can run concurrently
- Optimised content chunking for LLM processing
- Streaming results for better user experience

## Integration Points

### Streamlit Interface
- Real-time progress updates
- Interactive result display
- Export capabilities (YAML, JSON, summary)

### API Integration
- RESTful endpoints for programmatic access
- Webhook support for external integrations
- Batch processing capabilities

## Future Enhancements

### Planned Features
- Custom evaluation criteria configuration
- Multi-language document support
- Advanced analytics and reporting
- Integration with project management tools

### Scalability Improvements
- Distributed processing support
- Enhanced caching mechanisms
- Performance monitoring and optimisation 