from enum import Enum
from typing import Dict, Any, List, Optional, Union, Annotated
from pydantic import BaseModel, Field
from datetime import datetime
from operator import add


class MigrationStrategy(Enum):
    """6 R's Migration Strategy Classification"""
    REHOST = "rehost"  # Lift and shift
    REPLATFORM = "replatform"  # Lift, tinker, and shift
    REFACTOR = "refactor"  # Re-architect
    REPURCHASE = "repurchase"  # Move to SaaS
    RETIRE = "retire"  # Decommission
    RETAIN = "retain"  # Keep on-premises


class WorkloadComplexity(Enum):
    """Workload complexity classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    MULTI_CLOUD = "multi_cloud"


class GenAITool(Enum):
    """GenAI tools to be used in migration"""
    GITHUB_COPILOT = "github_copilot"
    AMAZON_Q = "amazon_q"
    MICROSOFT_365_COPILOT = "microsoft_365_copilot"
    Q_CODE_TRANSFORMATION = "q_code_transformation"
    LANGCHAIN = "langchain"
    CUSTOM_AI_AGENTS = "custom_ai_agents"


class DiscoveryInput(BaseModel):
    """Input structure for discovery data"""
    source_type: str = Field(description="Type of input: excel, json, text, csv")
    raw_data: Union[str, Dict[str, Any]] = Field(description="Raw discovery data")
    client_name: str = Field(description="Client organization name")
    project_name: str = Field(description="Migration project name")
    contact_info: Dict[str, str] = Field(default_factory=dict, description="Client contact information")
    business_context: Optional[str] = Field(None, description="Business drivers and context")
    
    # Additional context fields from UI
    business_drivers: List[str] = Field(default_factory=list, description="Primary business drivers")
    additional_context: Optional[str] = Field(None, description="Additional business context")
    target_cloud: Optional[str] = Field(None, description="Target cloud platform")
    migration_approach: Optional[str] = Field(None, description="Preferred migration approach")
    timeline_constraint: Optional[str] = Field(None, description="Timeline expectations")
    budget_constraint: Optional[str] = Field(None, description="Budget considerations")
    risk_tolerance: Optional[str] = Field(None, description="Risk tolerance level")
    compliance_requirements: List[str] = Field(default_factory=list, description="Compliance requirements")


class Application(BaseModel):
    """Individual application/workload definition"""
    name: str = Field(description="Application name")
    description: str = Field(description="Application description")
    technology_stack: List[str] = Field(description="Technologies used")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies on other apps/services")
    criticality: WorkloadComplexity = Field(description="Business criticality")
    current_environment: str = Field(description="Current hosting environment")
    data_classification: str = Field(default="internal", description="Data sensitivity level")
    compliance_requirements: List[str] = Field(default_factory=list, description="Regulatory requirements")
    estimated_users: Optional[int] = Field(None, description="Number of users")
    performance_requirements: Optional[str] = Field(None, description="Performance SLAs")


class WaveGroup(BaseModel):
    """Migration wave grouping"""
    wave_number: int = Field(description="Wave sequence number")
    name: str = Field(description="Wave name/description")
    applications: List[str] = Field(description="Application names in this wave")
    strategy: str = Field(description="Primary migration strategy for this wave")
    estimated_duration_weeks: int = Field(description="Estimated duration in weeks")
    dependencies: List[int] = Field(default_factory=list, description="Dependent wave numbers")
    risk_level: WorkloadComplexity = Field(description="Overall risk level")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites for this wave")


class ArchitectureRecommendation(BaseModel):
    """Cloud architecture recommendations"""
    cloud_provider: CloudProvider = Field(description="Recommended cloud provider")
    services: Dict[str, str] = Field(description="Recommended cloud services mapping")
    patterns: List[str] = Field(description="Recommended architecture patterns")
    security_controls: List[str] = Field(description="Security recommendations")
    cost_optimisation: List[str] = Field(description="Cost optimisation strategies")
    well_architected_pillars: Dict[str, str] = Field(description="Well-Architected Framework alignment")


class GenAIToolPlan(BaseModel):
    """GenAI tool usage plan"""
    tool: GenAITool = Field(description="GenAI tool")
    use_cases: List[str] = Field(description="Specific use cases")
    phases: List[str] = Field(description="Migration phases where tool will be used")
    expected_benefits: List[str] = Field(description="Expected benefits")
    implementation_notes: str = Field(description="Implementation guidance")


class SprintEstimate(BaseModel):
    """Sprint effort estimation"""
    wave_number: int = Field(description="Wave number")
    total_sprints: int = Field(description="Total number of sprints")
    sprint_duration_weeks: int = Field(default=2, description="Sprint duration in weeks")
    team_size: int = Field(description="Recommended team size")
    effort_breakdown: Dict[str, int] = Field(description="Effort breakdown by activity")
    assumptions: List[str] = Field(description="Key assumptions")
    risks: List[str] = Field(description="Identified risks")
    dependencies: List[str] = Field(description="External dependencies")


class ProposalSection(BaseModel):
    """Individual proposal section"""
    section_number: str = Field(description="Section number (e.g., '1.1')")
    title: str = Field(description="Section title")
    content: str = Field(description="Section content in markdown")
    subsections: List['ProposalSection'] = Field(default_factory=list, description="Nested subsections")


class ProposalState(BaseModel):
    """LangGraph state for proposal generation"""
    # Input data
    discovery_input: Optional[DiscoveryInput] = None
    
    # Parsed and classified data
    applications: List[Application] = Field(default_factory=list)
    workload_classification: Dict[str, Any] = Field(default_factory=dict)
    classified_workloads: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Planning outputs
    wave_groups: List[WaveGroup] = Field(default_factory=list)
    migration_waves: Dict[str, Any] = Field(default_factory=dict)
    migration_strategies: Dict[str, MigrationStrategy] = Field(default_factory=dict)
    modernisation_recommendations: Dict[str, Any] = Field(default_factory=dict)
    
    # Architecture and tooling
    architecture_recommendations: List[ArchitectureRecommendation] = Field(default_factory=list)
    genai_tool_plans: List[GenAIToolPlan] = Field(default_factory=list)
    
    # Effort estimation
    sprint_estimates: List[SprintEstimate] = Field(default_factory=list)
    
    # Generated content
    proposal_sections: List[ProposalSection] = Field(default_factory=list)
    overview_content: Optional[str] = None
    scope_content: Optional[str] = None
    
    # Output formats
    markdown_output: Optional[str] = None
    docx_path: Optional[str] = None
    pdf_path: Optional[str] = None
    
    # Versioning and feedback loops
    version: int = Field(default=1)
    feedback_loops: Annotated[List[str], add] = Field(default_factory=list)
    
    # Error handling - using Annotated to allow multiple nodes to add errors/warnings
    errors: Annotated[List[str], add] = Field(default_factory=list)
    warnings: Annotated[List[str], add] = Field(default_factory=list)


class ProposalTemplate(BaseModel):
    """Template configuration for proposal generation"""
    template_name: str = Field(description="Template identifier")
    sections: List[Dict[str, str]] = Field(description="Required sections with titles")
    formatting_rules: Dict[str, Any] = Field(description="Formatting specifications")
    client_branding: Dict[str, str] = Field(default_factory=dict, description="Client branding elements")
    output_formats: List[str] = Field(default=["markdown", "docx", "pdf"], description="Required output formats")


# Update ProposalSection to handle forward references
ProposalSection.model_rebuild() 