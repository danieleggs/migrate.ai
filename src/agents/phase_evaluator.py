from typing import Dict, Any, List
import yaml
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import time

from ..models.evaluation import GraphState, PhaseEvaluation, MigrationPhase, PhaseContent
from ..utils.json_parser import parse_llm_json_response, create_evaluation_fallback


class PhaseEvaluator:
    """Evaluates a specific migration phase against the specification."""
    
    def __init__(self, phase: MigrationPhase):
        self.phase = phase
        self.spec = self._load_spec()
    
    def _load_spec(self) -> Dict[str, Any]:
        """Load the migrate.ai specification."""
        spec_path = Path(__file__).parent.parent / "config" / "modernize_ai_spec.yaml"
        with open(spec_path, 'r') as f:
            return yaml.safe_load(f)
    
    def evaluate(self, content: str, context: Dict[str, Any] = None) -> PhaseEvaluation:
        """Evaluate the phase content against the specification."""
        
        phase_spec = self.spec["migrate_ai_specification"]["phases"][self.phase.value]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a migrate.ai evaluation expert. Your task is to evaluate the {self.phase.value.upper()} phase content against the migrate.ai Agent-Led Migration Specification.

Phase: {phase_spec['name']}
Description: {phase_spec['description']}

Workstreams to evaluate:
{self._format_workstreams(phase_spec['workstreams'])}

Evaluation criteria:
1. Completeness of workstream coverage
2. Quality of implementation approach
3. Alignment with migrate.ai principles
4. Technical feasibility and best practices
5. Risk management and mitigation strategies

Please provide:
1. Overall score (0-3): 0=Poor, 1=Basic, 2=Good, 3=Excellent
2. Strengths: What is done well
3. Weaknesses: What needs improvement
4. Evidence: Specific examples from the content
5. Recommendations: Specific improvements needed

Return your response as JSON with this structure:
{{
    "score": <number>,
    "strengths": [<list of strings>],
    "weaknesses": [<list of strings>],
    "evidence": [<list of strings>],
    "recommendations": [<list of strings>]
}}"""),
            ("user", f"Evaluate this {self.phase.value} phase content:\n\n{content}")
        ])
        
        response = llm.invoke(prompt.format_messages())
        
        # Parse the JSON response
        try:
            import json
            result = json.loads(response.content)
            
            return PhaseEvaluation(
                phase=self.phase,
                score=result.get("score", 0),
                strengths=result.get("strengths", []),
                weaknesses=result.get("weaknesses", []),
                evidence=result.get("evidence", []),
                recommendations=result.get("recommendations", [])
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback if JSON parsing fails
            return PhaseEvaluation(
                phase=self.phase,
                score=1,
                strengths=["Content provided for evaluation"],
                weaknesses=[f"Could not parse evaluation response: {str(e)}"],
                evidence=["Response parsing failed"],
                recommendations=["Please review the content format and try again"]
            )
    
    def _format_workstreams(self, workstreams: list) -> str:
        """Format workstreams for the prompt."""
        formatted = []
        for ws in workstreams:
            formatted.append(f"- {ws['name']}: {ws['description']}")
        return "\n".join(formatted)


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def create_phase_evaluator_node(phase: MigrationPhase):
    """Create a phase evaluator node for the given phase."""
    evaluator = PhaseEvaluator(phase)
    
    def evaluate_phase(state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the specific phase."""
        try:
            # Get the content for this phase
            phase_content = state.get("phase_content", {}).get(phase.value, "")
            
            if not phase_content:
                return {
                    "errors": [f"No content found for {phase.value} phase"]
                }
            
            # Evaluate the phase
            evaluation = evaluator.evaluate(phase_content)
            
            # Store the evaluation
            phase_evaluations = state.get("phase_evaluations", [])
            phase_evaluations.append(evaluation)
            
            return {
                "phase_evaluations": phase_evaluations
            }
            
        except Exception as e:
            return {
                "errors": [f"Phase evaluation failed for {phase.value}: {str(e)}"]
            }
    
    return evaluate_phase


# Create individual node functions for each stage
strategise_and_plan_evaluator_node = create_phase_evaluator_node(MigrationPhase.STRATEGISE_AND_PLAN)
migrate_and_modernise_evaluator_node = create_phase_evaluator_node(MigrationPhase.MIGRATE_AND_MODERNISE)
manage_and_optimise_evaluator_node = create_phase_evaluator_node(MigrationPhase.MANAGE_AND_OPTIMISE) 