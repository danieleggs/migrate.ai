from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph

from ..models.proposal_generation import ProposalState
# Import from separated agent files
from ..agents.parse_discovery_input import parse_discovery_input
from ..agents.workload_classifier import classify_workloads
from ..agents.content_generator import generate_overview_and_scope
from ..agents.wave_planner import plan_migration_waves
from ..agents.migration_strategist import classify_migration_strategies
from ..agents.proposal_formatter import format_proposal_sections, create_output_files

# Import remaining nodes from cleaned file
from ..agents.proposal_nodes import (
    provide_architecture_advice,
    plan_genai_tools,
    estimate_sprint_efforts
)


def should_replan_waves(state: ProposalState) -> bool:
    """Determine if wave planning needs to be updated based on modernisation bias feedback."""
    # Check if modernisation bias has upgraded complexity or changed strategies
    if hasattr(state, 'migration_strategies') and state.migration_strategies:
        for strategy in state.migration_strategies:
            if isinstance(strategy, dict):
                # Check if modernization opportunities suggest wave replanning
                modernization_opps = strategy.get('modernization_opportunities', [])
                if len(modernization_opps) > 2:  # Significant modernization potential
                    return True
                
                # Check if strategy changed from simple to complex
                if strategy.get('recommended_strategy') in ['refactor', 'repurchase']:
                    return True
    
    return False


def should_reclassify_strategies(state: ProposalState) -> bool:
    """Determine if 6R strategies need reclassification based on effort estimates."""
    # Check if effort estimates are too high, suggesting need for simpler strategies
    if hasattr(state, 'effort_estimates') and state.effort_estimates:
        effort_data = state.effort_estimates
        
        # Check total project duration
        total_weeks = effort_data.get('total_project_duration_weeks', 0)
        if total_weeks > 52:  # More than 1 year suggests need for simpler strategies
            return True
        
        # Check individual wave efforts
        wave_estimates = effort_data.get('wave_estimates', [])
        for wave in wave_estimates:
            if wave.get('effort_person_weeks', 0) > 100:  # Very high effort wave
                return True
    
    return False


def should_update_scope(state: ProposalState) -> bool:
    """Determine if scope needs updating based on architecture recommendations."""
    # Check if architecture recommendations suggest scope changes
    if hasattr(state, 'architecture_recommendations') and state.architecture_recommendations:
        arch_recs = state.architecture_recommendations
        
        # Check if complex architecture patterns are recommended
        patterns = arch_recs.get('architecture_patterns', [])
        complex_patterns = ['Microservices', 'Event-driven', 'Serverless-first']
        
        if any(pattern in patterns for pattern in complex_patterns):
            return True
        
        # Check if many new technologies are recommended
        tech_stack = arch_recs.get('technology_stack', {})
        total_services = sum(len(services) for services in tech_stack.values())
        if total_services > 10:  # Many services suggest scope expansion
            return True
    
    return False


def route_after_modernisation_bias(state: ProposalState) -> str:
    """Route after modernisation bias analysis."""
    # Check if we need to replan waves due to complexity upgrades
    if should_replan_waves(state):
        # Add feedback loop indicator
        if not hasattr(state, 'feedback_loops'):
            state.feedback_loops = []
        state.feedback_loops.append("modernisation_bias_triggered_wave_replan")
        return "wave_planning"
    else:
        return "architecture_advisor"


def route_after_architecture_advisor(state: ProposalState) -> str:
    """Route after architecture advisor."""
    # Check if architecture recommendations require scope updates
    if should_update_scope(state):
        if not hasattr(state, 'feedback_loops'):
            state.feedback_loops = []
        state.feedback_loops.append("architecture_complexity_triggered_scope_update")
        return "generate_scope"
    else:
        return "genai_tool_planner"


def route_after_effort_estimation(state: ProposalState) -> str:
    """Route after effort estimation."""
    # Check if effort is too high and we need to reclassify strategies
    if should_reclassify_strategies(state):
        if not hasattr(state, 'feedback_loops'):
            state.feedback_loops = []
        state.feedback_loops.append("effort_estimation_triggered_strategy_reclassification")
        return "migration_strategy_6rs"
    else:
        return "template_formatter"


def create_proposal_generation_graph() -> CompiledGraph:
    """Create the migration proposal generation workflow graph with recursive elements."""
    
    # Initialize the workflow
    workflow = StateGraph(ProposalState)
    
    # Add all nodes with original names to match the diagram
    workflow.add_node("parse_input", parse_discovery_input)
    workflow.add_node("classify_workloads", classify_workloads)
    
    # Split content generation into separate nodes
    workflow.add_node("generate_overview", lambda state: {
        "overview_content": generate_overview_and_scope(state).get("overview_content", "")
    })
    workflow.add_node("generate_scope", lambda state: {
        "scope_content": generate_overview_and_scope(state).get("scope_content", "")
    })
    
    workflow.add_node("wave_planning", plan_migration_waves)
    workflow.add_node("migration_strategy_6rs", classify_migration_strategies)
    
    # Create modernisation bias node (simplified version of migration strategist)
    workflow.add_node("modernisation_bias", lambda state: {
        "modernization_analysis": "Applied modernization bias to strategy recommendations"
    })
    
    workflow.add_node("architecture_advisor", provide_architecture_advice)
    workflow.add_node("genai_tool_planner", plan_genai_tools)
    workflow.add_node("sprint_effort_estimator", estimate_sprint_efforts)
    workflow.add_node("template_formatter", format_proposal_sections)
    workflow.add_node("pdf_creator", create_output_files)
    
    # Set entry point
    workflow.set_entry_point("parse_input")
    
    # Linear flow for initial processing
    workflow.add_edge("parse_input", "classify_workloads")
    
    # Parallel content generation after classification
    workflow.add_edge("classify_workloads", "generate_overview")
    workflow.add_edge("classify_workloads", "generate_scope")
    workflow.add_edge("classify_workloads", "wave_planning")
    workflow.add_edge("classify_workloads", "migration_strategy_6rs")
    
    # Strategy analysis flow
    workflow.add_edge("migration_strategy_6rs", "modernisation_bias")
    
    # Conditional routing after modernisation bias (feedback loop to wave planning)
    workflow.add_conditional_edges(
        "modernisation_bias",
        route_after_modernisation_bias,
        {
            "wave_planning": "wave_planning",  # Feedback loop
            "architecture_advisor": "architecture_advisor"
        }
    )
    
    # Architecture advisor flow
    workflow.add_conditional_edges(
        "architecture_advisor",
        route_after_architecture_advisor,
        {
            "generate_scope": "generate_scope",  # Feedback loop
            "genai_tool_planner": "genai_tool_planner"
        }
    )
    
    # Continue to effort estimation
    workflow.add_edge("genai_tool_planner", "sprint_effort_estimator")
    
    # Conditional routing after effort estimation (feedback loop to strategy reclassification)
    workflow.add_conditional_edges(
        "sprint_effort_estimator",
        route_after_effort_estimation,
        {
            "migration_strategy_6rs": "migration_strategy_6rs",  # Feedback loop
            "template_formatter": "template_formatter"
        }
    )
    
    # Final output generation
    workflow.add_edge("template_formatter", "pdf_creator")
    workflow.add_edge("pdf_creator", END)
    
    return workflow.compile()


class ProposalGenerationOrchestrator:
    """Main orchestrator for migration proposal generation with recursive feedback loops."""
    
    def __init__(self):
        self.graph = create_proposal_generation_graph()
    
    def generate_proposal(self, discovery_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a migration proposal from discovery data with intelligent feedback loops.
        
        Args:
            discovery_data: Discovery input data
            
        Returns:
            Dictionary containing proposal generation results
        """
        try:
            # Create initial state
            from ..models.proposal_generation import DiscoveryInput
            
            discovery_input = DiscoveryInput(**discovery_data)
            initial_state = ProposalState(
                discovery_input=discovery_input,
                feedback_loops=[],
                version=1
            )
            
            # Run the proposal generation graph
            final_state = self.graph.invoke(initial_state)
            
            # Check for errors
            if hasattr(final_state, 'errors') and final_state.errors:
                return {
                    "success": False,
                    "errors": final_state.errors,
                    "warnings": getattr(final_state, 'warnings', []),
                    "partial_results": self._extract_partial_results(final_state),
                    "feedback_loops": getattr(final_state, 'feedback_loops', []),
                    "iterations": getattr(final_state, 'version', 1)
                }
            
            # Return successful generation
            return {
                "success": True,
                "proposal_state": final_state,
                "outputs": {
                    "markdown_content": getattr(final_state, 'markdown_output', ''),
                    "formatted_sections": getattr(final_state, 'proposal_sections', [])
                },
                "warnings": getattr(final_state, 'warnings', []),
                "feedback_loops": getattr(final_state, 'feedback_loops', []),
                "iterations": getattr(final_state, 'version', 1),
                "metadata": {
                    "total_feedback_loops": len(getattr(final_state, 'feedback_loops', [])),
                    "final_version": getattr(final_state, 'version', 1),
                    "optimisation_applied": len(getattr(final_state, 'feedback_loops', [])) > 0
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "errors": [f"Proposal generation failed: {str(e)}"],
                "warnings": [],
                "partial_results": {},
                "feedback_loops": [],
                "iterations": 1
            }
    
    def _extract_partial_results(self, state: ProposalState) -> Dict[str, Any]:
        """Extract any partial results from a failed generation."""
        results = {}
        
        if hasattr(state, 'workload_classification') and state.workload_classification:
            results['workload_classification'] = state.workload_classification
        
        if hasattr(state, 'classified_workloads') and state.classified_workloads:
            results['classified_workloads'] = state.classified_workloads
        
        if hasattr(state, 'migration_waves') and state.migration_waves:
            results['migration_waves'] = state.migration_waves
        
        if hasattr(state, 'migration_strategies') and state.migration_strategies:
            results['migration_strategies'] = state.migration_strategies
        
        if hasattr(state, 'feedback_loops'):
            results['feedback_loops_triggered'] = state.feedback_loops
        
        if hasattr(state, 'version'):
            results['iterations_completed'] = state.version
        
        return results


def validate_proposal_completeness(state: ProposalState) -> List[str]:
    """Validate that all required proposal sections are complete."""
    missing_sections = []
    
    required_sections = [
        "overview",
        "scope",
        "wave_planning",
        "migration_strategy",
        "architecture",
        "genai_tooling",
        "effort_estimation"
    ]
    
    generated_section_titles = [section.title.lower() for section in state.proposal_sections]
    
    for required in required_sections:
        if not any(required in title for title in generated_section_titles):
            missing_sections.append(required)
    
    return missing_sections


def estimate_proposal_quality(state: ProposalState) -> Dict[str, Any]:
    """Estimate the quality and completeness of the generated proposal."""
    quality_metrics = {
        "completeness_score": 0.0,
        "detail_score": 0.0,
        "modernisation_score": 0.0,
        "automation_score": 0.0,
        "overall_score": 0.0
    }
    
    # Completeness score based on sections
    required_sections = 7
    completed_sections = len(state.proposal_sections)
    quality_metrics["completeness_score"] = min(completed_sections / required_sections, 1.0)
    
    # Detail score based on content length
    total_content_length = sum(len(section.content) for section in state.proposal_sections)
    quality_metrics["detail_score"] = min(total_content_length / 10000, 1.0)  # 10k chars target
    
    # Modernisation score based on refactor/replatform ratio
    total_apps = len(state.applications)
    if total_apps > 0:
        modern_strategies = sum(1 for strategy in state.migration_strategies.values() 
                             if strategy in [MigrationStrategy.REFACTOR, MigrationStrategy.REPLATFORM])
        quality_metrics["modernisation_score"] = modern_strategies / total_apps
    
    # Automation score based on GenAI tool coverage
    quality_metrics["automation_score"] = min(len(state.genai_tool_plans) / 4, 1.0)  # 4 tools target
    
    # Overall score
    quality_metrics["overall_score"] = (
        quality_metrics["completeness_score"] * 0.3 +
        quality_metrics["detail_score"] * 0.2 +
        quality_metrics["modernisation_score"] * 0.3 +
        quality_metrics["automation_score"] * 0.2
    )
    
    return quality_metrics 