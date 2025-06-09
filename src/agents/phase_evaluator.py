from typing import Dict, Any, List
import yaml
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import time

from ..models.evaluation import GraphState, PhaseEvaluation, MigrationPhase, PhaseContent
from ..utils.json_parser import parse_llm_json_response, create_evaluation_fallback


class PhaseEvaluatorAgent:
    """Agent responsible for evaluating a specific migration phase against Modernize.AI specification."""
    
    def __init__(self, llm: ChatOpenAI, phase: MigrationPhase):
        self.llm = llm
        self.phase = phase
        self.spec = self._load_specification()
        self.prompt = self._create_prompt()
    
    def _load_specification(self) -> Dict[str, Any]:
        """Load the Modernize.AI specification."""
        spec_path = Path(__file__).parent.parent / "config" / "modernize_ai_spec.yaml"
        with open(spec_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create evaluation prompt for the specific phase."""
        phase_spec = self.spec["modernize_ai_specification"]["phases"][self.phase.value]
        
        return ChatPromptTemplate.from_messages([
            ("system", f"""You are a Modernize.AI evaluation expert. Your task is to evaluate the {self.phase.value.upper()} phase content against the Modernize.AI Agent-Led Migration Specification.

PHASE SPECIFICATION:
{yaml.dump(phase_spec, default_flow_style=False)}

SCORING RUBRIC:
0: Not addressed or completely missing
1: Partially addressed with significant gaps
2: Adequately addressed with minor gaps  
3: Fully addressed and well-implemented

Evaluate based on:
1. Presence of required elements
2. Quality of implementation approach
3. Alignment with Modernize.AI principles
4. Evidence of GenAI/automation usage
5. Completeness of the approach

Be strict but fair in your evaluation."""),
            ("human", """PHASE CONTENT TO EVALUATE:
Relevant Content: {relevant_content}

Key Points: {key_points}

Confidence Score: {confidence_score}

Please evaluate this {phase} phase content and provide:

1. Score (0-3) based on the rubric
2. Criteria assessment for each evaluation criterion
3. Strengths identified in the content
4. Weaknesses or gaps identified
5. Specific evidence supporting your evaluation

Respond in JSON format:
{{
    "score": 0-3,
    "criteria_met": {{
        "criterion_name": true/false,
        ...
    }},
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "evidence": ["evidence1", "evidence2"],
    "detailed_analysis": "comprehensive analysis of the phase content"
}}""")
        ])
    
    def __call__(self, state: GraphState, phase: MigrationPhase) -> Dict[str, Any]:
        """Evaluate a specific migration phase."""
        try:
            # Add small delay to avoid rate limiting
            time.sleep(1)
            
            # Find the relevant phase content
            phase_content = None
            for pc in state.phase_contents:
                if pc.phase == phase:
                    phase_content = pc
                    break
            
            if not phase_content:
                return {"error": f"No content found for phase {phase.value}"}
            
            if phase_content.phase != self.phase:
                return {"error": f"Phase mismatch: expected {self.phase}, got {phase_content.phase}"}
            
            # Format key points for display
            key_points_str = "\n".join([f"- {point}" for point in phase_content.key_points])
            
            # Get LLM evaluation
            response = self.llm.invoke(
                self.prompt.format_messages(
                    relevant_content=phase_content.relevant_content,
                    key_points=key_points_str,
                    confidence_score=phase_content.confidence_score,
                    phase=self.phase.value
                )
            )
            
            # Parse LLM response with fallback
            try:
                evaluation = parse_llm_json_response(
                    response.content, 
                    fallback_data=create_evaluation_fallback(self.phase.value)
                )
            except Exception as e:
                evaluation = create_evaluation_fallback(self.phase.value)
            
            # Create PhaseEvaluation object
            phase_evaluation = PhaseEvaluation(
                phase=self.phase,
                score=int(evaluation.get("score", 0)),
                criteria_met=evaluation.get("criteria_met", {}),
                strengths=evaluation.get("strengths", []),
                weaknesses=evaluation.get("weaknesses", []),
                evidence=evaluation.get("evidence", [])
            )
            
            return {
                "phase_evaluation": phase_evaluation,
                "detailed_analysis": evaluation.get("detailed_analysis", "")
            }
            
        except Exception as e:
            return {"error": f"Error evaluating {self.phase.value} phase: {str(e)}"}


def create_phase_evaluator_node(phase: MigrationPhase):
    """Create a phase evaluator node for a specific migration phase."""
    
    def phase_evaluator_node(state: GraphState) -> Dict[str, Any]:
        """LangGraph node function for phase evaluation."""
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        agent = PhaseEvaluatorAgent(llm, phase)
        
        result = agent(state, phase)
        
        if "error" in result:
            return {"error": result["error"]}
        else:
            # Return the evaluation to be added to the state
            return {"phase_evaluations": [result["phase_evaluation"]]}
    
    return phase_evaluator_node


# Create individual node functions for each stage
strategise_and_plan_evaluator_node = create_phase_evaluator_node(MigrationPhase.STRATEGISE_AND_PLAN)
migrate_and_modernise_evaluator_node = create_phase_evaluator_node(MigrationPhase.MIGRATE_AND_MODERNISE)
manage_and_optimise_evaluator_node = create_phase_evaluator_node(MigrationPhase.MANAGE_AND_OPTIMISE) 