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
    """Evaluation result for a specific migration phase."""
    phase: MigrationPhase
    score: int = Field(ge=0, le=3)
    criteria_met: Dict[str, bool] = Field(default_factory=dict)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)


class SpecCompliance(BaseModel):
    """Compliance check against Modernize.AI specification."""
    compliant_areas: List[str] = Field(default_factory=list)
    non_compliant_areas: List[str] = Field(default_factory=list)
    missing_elements: List[str] = Field(default_factory=list)
    overall_compliance_score: float = Field(ge=0.0, le=1.0)


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
    """Final evaluation result."""
    scorecard: Dict[MigrationPhase, int] = Field(default_factory=dict)
    comments: Dict[MigrationPhase, str] = Field(default_factory=dict)
    phase_evaluations: List[PhaseEvaluation] = Field(default_factory=list)
    spec_compliance: SpecCompliance
    gaps: List[Gap] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    overall_score: float = Field(ge=0.0, le=3.0)
    summary: str


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