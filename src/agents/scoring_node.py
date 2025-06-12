"""
Scoring Node Agent

Agent responsible for calculating final evaluation scores.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import FinalScore
from ..utils.json_parser import parse_llm_json_response

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a migrate.ai scoring expert. Your task is to calculate the final evaluation score based on all the analysis components.

Consider the following factors in your scoring:
1. Phase evaluation scores and quality
2. Specification compliance level
3. Gap analysis severity and frequency
4. Overall alignment with migrate.ai principles
5. Technical approach quality and feasibility

Scoring methodology:
- Phase Scores: Weight each phase evaluation (0-3 scale)
- Compliance Score: Overall specification compliance (0.0-1.0 scale)
- Gap Penalty: Reduce score based on critical and high-priority gaps
- Quality Bonus: Add points for exceptional alignment and innovation

Final score should be on a 0-100 scale:
- 90-100: Exceptional alignment with migrate.ai specification
- 80-89: Strong alignment with minor improvements needed
- 70-79: Good alignment with some gaps to address
- 60-69: Adequate alignment with significant improvements needed
- 50-59: Poor alignment with major gaps
- 0-49: Inadequate alignment requiring substantial rework

Return your response as JSON with this structure:
{{
    "final_score": <number between 0-100>,
    "score_breakdown": {{
        "phase_scores": <weighted average of phase scores>,
        "compliance_score": <specification compliance contribution>,
        "gap_penalty": <points deducted for gaps>,
        "quality_bonus": <points added for excellence>
    }},
    "score_rationale": "explanation of how the score was calculated",
    "grade": "A|B|C|D|F based on final score"
}}"""),
    ("user", """Calculate the final evaluation score using the migrate.ai scoring methodology.

PHASE EVALUATIONS:
{phase_evaluations}

SPECIFICATION COMPLIANCE:
{spec_compliance}

GAP ANALYSIS:
{gap_analysis}

Please calculate the final score and provide detailed breakdown.""")
])

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def scoring_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node function for final scoring."""
    try:
        # Get evaluation results
        phase_evaluations = state.get("phase_evaluations", [])
        spec_compliance = state.get("spec_compliance")
        gap_analysis = state.get("gap_analysis")
        
        # Format phase evaluations
        phase_eval_text = ""
        total_phase_score = 0
        for eval in phase_evaluations:
            phase_eval_text += f"\n{eval.phase.value.upper()} Phase: {eval.score}/3\n"
            total_phase_score += eval.score
        
        if phase_evaluations:
            avg_phase_score = total_phase_score / len(phase_evaluations)
            phase_eval_text += f"\nAverage Phase Score: {avg_phase_score:.2f}/3"
        
        # Format spec compliance
        spec_text = ""
        if spec_compliance:
            spec_text = f"Overall Compliance Score: {spec_compliance.overall_compliance_score:.2f}/1.0\n"
            spec_text += f"Missing Elements: {len(spec_compliance.missing_elements)}\n"
            spec_text += f"Improvement Areas: {len(spec_compliance.improvement_areas)}"
        
        # Format gap analysis
        gap_text = ""
        if gap_analysis:
            gap_text += f"Critical Gaps: {len(gap_analysis.critical_gaps)}\n"
            gap_text += f"High Priority Gaps: {len(gap_analysis.high_priority_gaps)}\n"
            gap_text += f"Medium Priority Gaps: {len(gap_analysis.medium_priority_gaps)}\n"
            gap_text += f"Low Priority Gaps: {len(gap_analysis.low_priority_gaps)}"
        
        # Get LLM scoring
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
                "final_score": 50,
                "score_breakdown": {
                    "phase_scores": 1.5,
                    "compliance_score": 0.5,
                    "gap_penalty": -10,
                    "quality_bonus": 0
                },
                "score_rationale": "Could not parse scoring response",
                "grade": "C"
            }
        )
        
        final_score = FinalScore(
            final_score=result.get("final_score", 50),
            score_breakdown=result.get("score_breakdown", {}),
            score_rationale=result.get("score_rationale", ""),
            grade=result.get("grade", "C")
        )
        
        return {
            "final_score": final_score
        }
        
    except Exception as e:
        return {
            "errors": [f"Scoring calculation failed: {str(e)}"]
        } 