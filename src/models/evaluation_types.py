"""
Evaluation types and configurations for the Pre-Sales Document Evaluator.
"""

from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel


class EvaluationType(Enum):
    """Types of document evaluation available."""
    MIGRATION_PROPOSAL = "migration_proposal"
    STATEMENT_OF_WORK = "statement_of_work"
    PROPOSAL_GENERATOR = "proposal_generator"


class EvaluationConfig(BaseModel):
    """Configuration for a specific evaluation type."""
    name: str
    description: str
    icon: str
    spec_file: str
    phases: List[str]
    evaluation_criteria: List[str]


# Configuration for each evaluation type
EVALUATION_CONFIGS: Dict[EvaluationType, EvaluationConfig] = {
    EvaluationType.MIGRATION_PROPOSAL: EvaluationConfig(
        name="Migration Proposal Evaluation",
        description="Comprehensive evaluation of migration proposals against migrate.ai specification framework",
        icon="",
        spec_file="config/migration_spec.yaml",
        phases=["strategise_and_plan", "migrate_and_modernise", "manage_and_optimise"],
        evaluation_criteria=[
            "Strategic alignment with business objectives",
            "Technical approach and architecture quality",
            "Risk management and mitigation strategies",
            "Timeline and resource planning",
            "Cost estimation and business case",
            "Team capability and readiness assessment",
            "Automation and tooling strategy",
            "Compliance with migrate.ai principles"
        ]
    ),
    
    EvaluationType.STATEMENT_OF_WORK: EvaluationConfig(
        name="SOW Framework Evaluation",
        description="Assessment of Statement of Work documents for completeness and quality",
        icon="",
        spec_file="config/sow_spec.yaml", 
        phases=["scope_definition", "dependencies_analysis", "assumptions_review"],
        evaluation_criteria=[
            "Scope definition and clarity",
            "Deliverables specification",
            "Timeline and milestones",
            "Resource allocation",
            "Risk and assumption management",
            "Success criteria definition",
            "Commercial terms alignment",
            "Governance and communication framework"
        ]
    ),
    
    EvaluationType.PROPOSAL_GENERATOR: EvaluationConfig(
        name="Migration Proposal Generator",
        description="Generate comprehensive migration proposals from discovery data using migrate.ai methodology",
        icon="",
        spec_file="",  # Not needed for generator
        phases=["discovery_analysis", "wave_planning", "strategy_classification", "proposal_generation"],
        evaluation_criteria=[
            "Discovery data analysis and insights",
            "Application portfolio assessment",
            "Migration wave planning and sequencing",
            "Technology stack evaluation",
            "Risk assessment and mitigation",
            "Resource and timeline estimation",
            "Business case development",
            "Implementation roadmap creation"
        ]
    )
} 