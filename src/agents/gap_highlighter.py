"""
Gap Highlighter Agent

Agent responsible for identifying gaps and weaknesses in migration proposals.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import GapAnalysis
from ..utils.json_parser import parse_llm_json_response

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a migrate.ai gap analysis expert. Your task is to identify specific gaps and weaknesses in the proposal based on the phase evaluations and specification compliance analysis.

Focus on:
1. Critical gaps that could lead to project failure
2. High-priority gaps that significantly impact success
3. Medium-priority gaps that should be addressed
4. Missing elements from the migrate.ai specification
5. Areas where the proposal deviates from best practices

For each gap identified, provide:
- Clear description of what is missing or inadequate
- Impact level (CRITICAL, HIGH, MEDIUM, LOW)
- Specific recommendations for addressing the gap
- Evidence from the proposal content

Return your response as JSON with this structure:
{{
    "critical_gaps": [
        {{
            "description": "gap description",
            "impact": "explanation of impact",
            "recommendation": "specific recommendation",
            "evidence": "supporting evidence"
        }}
    ],
    "high_priority_gaps": [...],
    "medium_priority_gaps": [...],
    "low_priority_gaps": [...]
}}"""),
    ("user", """Based on the following evaluation results, identify specific gaps and weaknesses:

PHASE EVALUATIONS:
{phase_evaluations}

SPECIFICATION COMPLIANCE:
{spec_compliance}

DOCUMENT CONTENT:
{document_content}

Please identify and categorise gaps by priority level.""")
])

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def gap_highlighter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node function for gap analysis."""
    try:
        # Get evaluation results
        phase_evaluations = state.get("phase_evaluations", [])
        spec_compliance = state.get("spec_compliance")
        document_content = state.get("document_content", "")
        
        # Format phase evaluations for the prompt
        phase_eval_text = ""
        for eval in phase_evaluations:
            phase_eval_text += f"\n{eval.phase.value.upper()} Phase (Score: {eval.score}/3):\n"
            phase_eval_text += f"Strengths: {', '.join(eval.strengths)}\n"
            phase_eval_text += f"Weaknesses: {', '.join(eval.weaknesses)}\n"
        
        # Format spec compliance
        spec_text = ""
        if spec_compliance:
            spec_text = f"Overall Compliance: {spec_compliance.overall_compliance_score:.2f}\n"
            spec_text += f"Missing Elements: {', '.join(spec_compliance.missing_elements)}\n"
            spec_text += f"Improvement Areas: {', '.join(spec_compliance.improvement_areas)}\n"
        
        # Get LLM analysis
        response = llm.invoke(
            prompt.format_messages(
                phase_evaluations=phase_eval_text,
                spec_compliance=spec_text,
                document_content=document_content[:2000]  # Limit content length
            )
        )
        
        # Parse response
        result = parse_llm_json_response(
            response.content,
            fallback_data={
                "critical_gaps": [],
                "high_priority_gaps": [],
                "medium_priority_gaps": [],
                "low_priority_gaps": []
            }
        )
        
        gap_analysis = GapAnalysis(
            critical_gaps=result.get("critical_gaps", []),
            high_priority_gaps=result.get("high_priority_gaps", []),
            medium_priority_gaps=result.get("medium_priority_gaps", []),
            low_priority_gaps=result.get("low_priority_gaps", [])
        )
        
        return {
            "gap_analysis": gap_analysis
        }
        
    except Exception as e:
        return {
            "errors": [f"Gap analysis failed: {str(e)}"]
        } 