"""
Recommendations Generator Agent

Agent responsible for generating actionable recommendations to improve migrate.ai alignment.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import Recommendations
from ..utils.json_parser import parse_llm_json_response

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a migrate.ai consultant expert. Your task is to generate specific, actionable recommendations to improve the proposal's alignment with migrate.ai Agent-Led Migration Specification.

Focus on providing recommendations that address:
1. Identified gaps and weaknesses
2. Enhancing compliance with migrate.ai principles
3. Improving technical approach and implementation
4. Strengthening risk management and mitigation
5. Optimising automation and AI integration

Categorise recommendations by priority:
- CRITICAL: Essential for project success and migrate.ai alignment
- HIGH: Important improvements that significantly enhance the proposal
- MEDIUM: Beneficial enhancements that add value
- LOW: Nice-to-have improvements for completeness

For each recommendation, provide:
- Clear, actionable description
- Rationale explaining why it's important
- Implementation guidance or next steps
- Expected impact on proposal quality

Return your response as JSON with this structure:
{{
    "critical_recommendations": [
        {{
            "description": "specific actionable recommendation",
            "rationale": "why this is important",
            "implementation": "how to implement this",
            "impact": "expected improvement"
        }}
    ],
    "high_priority_recommendations": [...],
    "medium_priority_recommendations": [...],
    "low_priority_recommendations": [...]
}}"""),
    ("user", """Based on the evaluation results, generate specific recommendations:

PHASE EVALUATIONS:
{phase_evaluations}

SPECIFICATION COMPLIANCE:
{spec_compliance}

GAP ANALYSIS:
{gap_analysis}

Please generate actionable recommendations to improve alignment with migrate.ai specification.""")
])

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def recommendations_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node function for generating recommendations."""
    try:
        # Get evaluation results
        phase_evaluations = state.get("phase_evaluations", [])
        spec_compliance = state.get("spec_compliance")
        gap_analysis = state.get("gap_analysis")
        
        # Format phase evaluations
        phase_eval_text = ""
        for eval in phase_evaluations:
            phase_eval_text += f"\n{eval.phase.value.upper()} Phase (Score: {eval.score}/3):\n"
            phase_eval_text += f"Weaknesses: {', '.join(eval.weaknesses)}\n"
            phase_eval_text += f"Recommendations: {', '.join(eval.recommendations)}\n"
        
        # Format spec compliance
        spec_text = ""
        if spec_compliance:
            spec_text = f"Overall Compliance: {spec_compliance.overall_compliance_score:.2f}\n"
            spec_text += f"Missing Elements: {', '.join(spec_compliance.missing_elements)}\n"
            spec_text += f"Recommendations: {', '.join(spec_compliance.recommendations)}\n"
        
        # Format gap analysis
        gap_text = ""
        if gap_analysis:
            gap_text += f"Critical Gaps: {len(gap_analysis.critical_gaps)}\n"
            gap_text += f"High Priority Gaps: {len(gap_analysis.high_priority_gaps)}\n"
            gap_text += f"Medium Priority Gaps: {len(gap_analysis.medium_priority_gaps)}\n"
        
        # Get LLM recommendations
        response = llm.invoke(
            prompt.format_messages(
                phase_evaluations=phase_eval_text,
                spec_compliance=spec_text,
                gap_analysis=gap_text
            )
        )
        
        # Parse response
        result = parse_llm_json_response(
            response.content,
            fallback_data={
                "critical_recommendations": [],
                "high_priority_recommendations": [],
                "medium_priority_recommendations": [],
                "low_priority_recommendations": []
            }
        )
        
        recommendations = Recommendations(
            critical_recommendations=result.get("critical_recommendations", []),
            high_priority_recommendations=result.get("high_priority_recommendations", []),
            medium_priority_recommendations=result.get("medium_priority_recommendations", []),
            low_priority_recommendations=result.get("low_priority_recommendations", [])
        )
        
        return {
            "recommendations": recommendations
        }
        
    except Exception as e:
        return {
            "errors": [f"Recommendations generation failed: {str(e)}"]
        } 