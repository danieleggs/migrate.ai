from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel


class EvaluationType(Enum):
    """Different types of document evaluations available."""
    MIGRATION_PROPOSAL = "migration_proposal"
    STATEMENT_OF_WORK = "statement_of_work"
    PROPOSAL_GENERATOR = "proposal_generator"


class EvaluationConfig(BaseModel):
    """Configuration for each evaluation type."""
    name: str
    description: str
    icon: str
    spec_file: str
    phases: List[str]
    evaluation_criteria: List[str]


# Configuration for each evaluation type
EVALUATION_CONFIGS: Dict[EvaluationType, EvaluationConfig] = {
    EvaluationType.MIGRATION_PROPOSAL: EvaluationConfig(
        name="Migration Proposal",
        description="Comprehensive evaluation of migration proposals against Modernize.AI specification framework",
        icon="",
        spec_file="config/migration_spec.yaml",
        phases=["strategise_and_plan", "migrate_and_modernise", "manage_and_optimise"],
        evaluation_criteria=[
            "Technical architecture alignment",
            "Migration strategy completeness", 
            "Risk assessment and mitigation",
            "Timeline and resource planning",
            "Compliance with industry standards"
        ]
    ),
    
    EvaluationType.STATEMENT_OF_WORK: EvaluationConfig(
        name="SOW Framework",
        description="Framework for evaluating Statement of Work documents for scope, dependencies, and assumptions",
        icon="",
        spec_file="config/sow_spec.yaml", 
        phases=["scope_definition", "dependencies_analysis", "assumptions_review"],
        evaluation_criteria=[
            "Scope clarity and completeness",
            "Dependency identification and management",
            "Assumption documentation and validation",
            "Risk assessment coverage",
            "Deliverable specifications"
        ]
    ),
    
    EvaluationType.PROPOSAL_GENERATOR: EvaluationConfig(
        name="Migration Proposal Generator",
        description="Generate comprehensive migration proposals from discovery data using Modernize.AI methodology",
        icon="",
        spec_file="",  # Not needed for generator
        phases=["discovery_analysis", "wave_planning", "strategy_classification", "proposal_generation"],
        evaluation_criteria=[
            "Discovery data analysis and application classification",
            "Wave-based migration planning with dual-track methodology", 
            "6 R's strategy classification with modernization bias",
            "Architecture recommendations and GenAI tool planning",
            "Sprint estimation and comprehensive proposal generation"
        ]
    )
} 