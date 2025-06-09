from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.graph.graph import CompiledGraph

from ..models.evaluation import GraphState, ParsedDocument, MigrationPhase
from ..utils.document_parser import DocumentParser
from ..agents.parse_input_doc import parse_input_doc_node
from ..agents.extract_intent_and_phases import extract_intent_and_phases_node
from ..agents.phase_evaluator import (
    strategise_and_plan_evaluator_node,
    migrate_and_modernise_evaluator_node,
    manage_and_optimise_evaluator_node
)
from ..agents.spec_checker import spec_checker_node
from ..agents.gap_highlighter import gap_highlighter_node
from ..agents.recommendations_generator import recommendations_generator_node
from ..agents.scoring_node import scoring_node


def should_evaluate_phase(state: GraphState, phase: MigrationPhase) -> bool:
    """Determine if a phase should be evaluated based on content relevance."""
    # Find the phase content for this phase
    for phase_content in state.phase_contents:
        if phase_content.phase == phase:
            # Only evaluate if confidence score is above threshold (increased to 0.5 for better selectivity)
            # and there's actual relevant content
            return (phase_content.confidence_score > 0.5 and 
                   phase_content.relevant_content != "No relevant content identified")
    return False


def route_after_phase_extraction(state: GraphState) -> List[str]:
    """Route to only the relevant phase evaluators based on content analysis."""
    next_nodes = []
    
    print("DEBUG ROUTING: Phase content analysis:")
    for phase_content in state.phase_contents:
        print(f"  {phase_content.phase.value}: confidence={phase_content.confidence_score:.2f}, content='{phase_content.relevant_content[:100]}...'")
    
    # Check each phase and only route to evaluators for relevant phases
    if should_evaluate_phase(state, MigrationPhase.STRATEGISE_AND_PLAN):
        next_nodes.append("strategise_and_plan_evaluator")
        print("DEBUG ROUTING: Adding strategise_and_plan_evaluator")
    
    if should_evaluate_phase(state, MigrationPhase.MIGRATE_AND_MODERNISE):
        next_nodes.append("migrate_and_modernise_evaluator")
        print("DEBUG ROUTING: Adding migrate_and_modernise_evaluator")
    
    if should_evaluate_phase(state, MigrationPhase.MANAGE_AND_OPTIMISE):
        next_nodes.append("manage_and_optimise_evaluator")
        print("DEBUG ROUTING: Adding manage_and_optimise_evaluator")
    
    # If no phases are relevant enough, still run at least one evaluator
    # to provide feedback on why the document doesn't align
    if not next_nodes:
        print("DEBUG ROUTING: No phases above threshold, selecting best phase")
        # Find the phase with highest confidence score
        best_phase = None
        best_score = 0
        for phase_content in state.phase_contents:
            if phase_content.confidence_score > best_score:
                best_score = phase_content.confidence_score
                best_phase = phase_content.phase
        
        print(f"DEBUG ROUTING: Best phase is {best_phase.value if best_phase else 'None'} with score {best_score}")
        
        if best_phase == MigrationPhase.STRATEGISE_AND_PLAN:
            next_nodes.append("strategise_and_plan_evaluator")
        elif best_phase == MigrationPhase.MIGRATE_AND_MODERNISE:
            next_nodes.append("migrate_and_modernise_evaluator")
        else:
            next_nodes.append("manage_and_optimise_evaluator")
    
    print(f"DEBUG ROUTING: Final routing decision: {next_nodes}")
    return next_nodes


def create_evaluation_graph() -> CompiledGraph:
    """Create the evaluation workflow graph with conditional routing."""
    
    # Initialize the workflow
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("parse_input_doc", parse_input_doc_node)
    workflow.add_node("extract_intent_and_phases", extract_intent_and_phases_node)
    workflow.add_node("strategise_and_plan_evaluator", strategise_and_plan_evaluator_node)
    workflow.add_node("migrate_and_modernise_evaluator", migrate_and_modernise_evaluator_node)
    workflow.add_node("manage_and_optimise_evaluator", manage_and_optimise_evaluator_node)
    workflow.add_node("spec_checker", spec_checker_node)
    workflow.add_node("gap_highlighter", gap_highlighter_node)
    workflow.add_node("recommendations_generator", recommendations_generator_node)
    workflow.add_node("scoring", scoring_node)
    
    # Set entry point
    workflow.set_entry_point("parse_input_doc")
    
    # Add edges
    workflow.add_edge("parse_input_doc", "extract_intent_and_phases")
    
    # Conditional routing based on phase relevance
    workflow.add_conditional_edges(
        "extract_intent_and_phases",
        route_after_phase_extraction,
        {
            "strategise_and_plan_evaluator": "strategise_and_plan_evaluator",
            "migrate_and_modernise_evaluator": "migrate_and_modernise_evaluator", 
            "manage_and_optimise_evaluator": "manage_and_optimise_evaluator"
        }
    )
    
    # All phase evaluators feed into spec checker
    workflow.add_edge("strategise_and_plan_evaluator", "spec_checker")
    workflow.add_edge("migrate_and_modernise_evaluator", "spec_checker")
    workflow.add_edge("manage_and_optimise_evaluator", "spec_checker")
    
    # Sequential flow after spec checker
    workflow.add_edge("spec_checker", "gap_highlighter")
    workflow.add_edge("gap_highlighter", "recommendations_generator")
    workflow.add_edge("recommendations_generator", "scoring")
    workflow.add_edge("scoring", END)
    
    return workflow.compile()


class EvaluationOrchestrator:
    """Main orchestrator for the evaluation process."""
    
    def __init__(self):
        self.graph = create_evaluation_graph()
    
    def evaluate_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Evaluate a document through the complete pipeline.
        
        Args:
            file_content: Raw file content as bytes
            filename: Name of the file for parsing
            
        Returns:
            Dictionary containing evaluation results or error information
        """
        try:
            # Parse the document first
            parsed_doc = DocumentParser.parse_document(file_content, filename)
            
            # Create initial state
            initial_state = GraphState(parsed_document=parsed_doc)
            
            # Run the evaluation graph
            final_state = self.graph.invoke(initial_state)
            
            # Check for errors - access state attributes properly
            error = getattr(final_state, 'error', None) or final_state.get('error', None)
            if error:
                return {
                    "success": False,
                    "error": error,
                    "partial_results": self._extract_partial_results(final_state)
                }
            
            # Return successful evaluation
            evaluation_result = getattr(final_state, 'evaluation_result', None) or final_state.get('evaluation_result', None)
            if evaluation_result:
                parsed_doc_attr = getattr(final_state, 'parsed_document', None) or final_state.get('parsed_document', None)
                phase_evaluations = getattr(final_state, 'phase_evaluations', []) or final_state.get('phase_evaluations', [])
                gaps = getattr(final_state, 'gaps', []) or final_state.get('gaps', [])
                recommendations = getattr(final_state, 'recommendations', []) or final_state.get('recommendations', [])
                
                return {
                    "success": True,
                    "evaluation_result": evaluation_result,
                    "metadata": {
                        "document_info": {
                            "filename": filename,
                            "document_type": parsed_doc.document_type.value,
                            "sections_found": list(parsed_doc.sections.keys()),
                            "content_length": len(parsed_doc.content)
                        },
                        "processing_info": {
                            "phases_evaluated": len(phase_evaluations),
                            "gaps_identified": len(gaps),
                            "recommendations_generated": len(recommendations)
                        }
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Evaluation completed but no results generated",
                    "partial_results": self._extract_partial_results(final_state)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Evaluation failed: {str(e)}",
                "partial_results": None
            }
    
    def _extract_partial_results(self, state) -> Dict[str, Any]:
        """Extract any partial results from a failed evaluation."""
        partial = {}
        
        parsed_document = getattr(state, 'parsed_document', None) or state.get('parsed_document', None)
        if parsed_document:
            partial["document_parsed"] = True
            partial["document_type"] = parsed_document.document_type.value
            partial["sections_found"] = len(parsed_document.sections)
        
        phase_contents = getattr(state, 'phase_contents', []) or state.get('phase_contents', [])
        if phase_contents:
            partial["phase_contents_extracted"] = len(phase_contents)
        
        phase_evaluations = getattr(state, 'phase_evaluations', []) or state.get('phase_evaluations', [])
        if phase_evaluations:
            partial["phases_evaluated"] = len(phase_evaluations)
            partial["phase_scores"] = {
                eval.phase.value: eval.score 
                for eval in phase_evaluations
            }
        
        spec_compliance = getattr(state, 'spec_compliance', None) or state.get('spec_compliance', None)
        if spec_compliance:
            partial["compliance_checked"] = True
            partial["compliance_score"] = spec_compliance.overall_compliance_score
        
        gaps = getattr(state, 'gaps', []) or state.get('gaps', [])
        if gaps:
            partial["gaps_identified"] = len(gaps)
        
        recommendations = getattr(state, 'recommendations', []) or state.get('recommendations', [])
        if recommendations:
            partial["recommendations_generated"] = len(recommendations)
        
        return partial


# Convenience function for direct usage
def evaluate_document(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Convenience function to evaluate a document.
    
    Args:
        file_content: Raw file content as bytes
        filename: Name of the file
        
    Returns:
        Evaluation results dictionary
    """
    orchestrator = EvaluationOrchestrator()
    return orchestrator.evaluate_document(file_content, filename) 