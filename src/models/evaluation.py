from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from typing_extensions import Annotated


class MigrationPhase(str, Enum):
    STRATEGISE_AND_PLAN = "strategise_and_plan"
    MIGRATE_AND_MODERNISE = "migrate_and_modernise"
    MANAGE_AND_OPTIMISE = "manage_and_optimise"


class DocumentType(str, Enum):
    RFP = "rfp"
    PROPOSAL = "proposal"
    RESPONSE = "response"
    OTHER = "other"


class ParsedDocument(BaseModel):
    """Structured representation of the input document."""
    content: str
    document_type: DocumentType
    sections: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PhaseContent(BaseModel):
    """Content mapped to a specific migration phase."""
    phase: MigrationPhase
    relevant_content: str
    key_points: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)


class PhaseEvaluation(BaseModel):
    """Evaluation results for a specific migration phase."""
    phase: MigrationPhase
    score: int = Field(ge=0, le=3, description="Phase score from 0-3")
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class SpecCompliance(BaseModel):
    """Compliance check against migrate.ai specification."""
    overall_compliance_score: float = Field(ge=0.0, le=1.0)
    missing_elements: List[str] = Field(default_factory=list)
    compliance_strengths: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class GapAnalysis(BaseModel):
    """Gap analysis results categorised by priority."""
    critical_gaps: List[Dict[str, str]] = Field(default_factory=list)
    high_priority_gaps: List[Dict[str, str]] = Field(default_factory=list)
    medium_priority_gaps: List[Dict[str, str]] = Field(default_factory=list)
    low_priority_gaps: List[Dict[str, str]] = Field(default_factory=list)


class Recommendations(BaseModel):
    """Recommendations categorised by priority."""
    critical_recommendations: List[Dict[str, str]] = Field(default_factory=list)
    high_priority_recommendations: List[Dict[str, str]] = Field(default_factory=list)
    medium_priority_recommendations: List[Dict[str, str]] = Field(default_factory=list)
    low_priority_recommendations: List[Dict[str, str]] = Field(default_factory=list)


class FinalScore(BaseModel):
    """Final evaluation score and breakdown."""
    final_score: int = Field(ge=0, le=100)
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    score_rationale: str = ""
    grade: str = "C"


class Gap(BaseModel):
    """Identified gap in the proposal."""
    area: str
    severity: str = Field(pattern="^(low|medium|high|critical)$")
    description: str
    impact: str
    phase: Optional[MigrationPhase] = None


class Recommendation(BaseModel):
    """Recommendation for improving alignment."""
    title: str
    description: str
    priority: str = Field(pattern="^(low|medium|high|critical)$")
    phase: Optional[MigrationPhase] = None
    implementation_effort: str = Field(pattern="^(low|medium|high)$")


class EvaluationResult(BaseModel):
    """Complete evaluation result."""
    phase_evaluations: List[PhaseEvaluation] = Field(default_factory=list)
    spec_compliance: Optional[SpecCompliance] = None
    gap_analysis: Optional[GapAnalysis] = None
    recommendations: Optional[Recommendations] = None
    final_score: Optional[FinalScore] = None
    errors: List[str] = Field(default_factory=list)


def add_to_list(existing: List, new: List) -> List:
    """Custom reducer to concatenate lists."""
    if existing is None:
        existing = []
    if new is None:
        new = []
    return existing + new


def keep_latest(existing: Optional[ParsedDocument], new: Optional[ParsedDocument]) -> Optional[ParsedDocument]:
    """Custom reducer to keep the latest non-None value."""
    if new is not None:
        return new
    return existing


def keep_first_error(existing: Optional[str], new: Optional[str]) -> Optional[str]:
    """Custom reducer to keep the first error encountered."""
    if existing is not None:
        return existing
    return new


class GraphState(BaseModel):
    """State object passed between LangGraph nodes."""
    parsed_document: Annotated[Optional[ParsedDocument], keep_latest] = None
    phase_contents: Annotated[List[PhaseContent], add_to_list] = Field(default_factory=list)
    phase_evaluations: Annotated[List[PhaseEvaluation], add_to_list] = Field(default_factory=list)
    spec_compliance: Optional[SpecCompliance] = None
    gaps: Annotated[List[Gap], add_to_list] = Field(default_factory=list)
    recommendations: Annotated[List[Recommendation], add_to_list] = Field(default_factory=list)
    evaluation_result: Optional[EvaluationResult] = None
    error: Annotated[Optional[str], keep_first_error] = None 