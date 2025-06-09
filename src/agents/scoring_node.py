from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import GraphState, EvaluationResult, MigrationPhase


class ScoringNodeAgent:
    """Agent responsible for calculating final scores and creating summary evaluation."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Modernize.AI scoring expert. Your task is to calculate the final evaluation score based on all the analysis components.

Scoring methodology:
1. Phase scores (0-3 each): Weight 60%
2. Specification compliance (0-1): Weight 25%
3. Gap severity impact: Weight 15%

Calculate:
- Individual phase scores and percentages
- Overall weighted score
- Compliance percentage
- Gap impact adjustment
- Final score and grade

Provide detailed scoring breakdown and rationale."""),
            ("human", """EVALUATION DATA:

Phase Evaluations:
{phase_evaluations}

Specification Compliance Score: {compliance_score}

Gaps Summary:
{gaps_summary}

Calculate the final evaluation score using the Modernize.AI scoring methodology.

Provide:
1. Individual phase scores and percentages
2. Weighted phase score contribution (60%)
3. Compliance score contribution (25%)
4. Gap impact adjustment (15%)
5. Final overall score (0-100)
6. Letter grade (A/B/C/D/F)
7. Detailed scoring rationale

Respond in JSON format:
{{
    "phase_scores": {{
        "strategise_and_plan": {{"score": 0-3, "percentage": 0-100}},
        "migrate_and_modernise": {{"score": 0-3, "percentage": 0-100}},
        "manage_and_optimise": {{"score": 0-3, "percentage": 0-100}}
    }},
    "compliance_percentage": 0-100,
    "gap_impact_score": 0-100,
    "weighted_scores": {{
        "phases_contribution": 0-60,
        "compliance_contribution": 0-25,
        "gap_impact_contribution": 0-15
    }},
    "final_score": 0-100,
    "letter_grade": "A|B|C|D|F",
    "scoring_rationale": "detailed explanation of scoring"
}}""")
        ])
    
    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """Calculate final scores and create evaluation summary."""
        try:
            if not state.phase_evaluations or not state.spec_compliance:
                return {"error": "Missing evaluation data for scoring"}
            
            doc = state.parsed_document
            
            # Calculate phase scores
            scorecard = {}
            comments = {}
            total_score = 0
            
            for eval in state.phase_evaluations:
                scorecard[eval.phase] = eval.score
                total_score += eval.score
                
                # Create phase comment
                strengths_str = ", ".join(eval.strengths[:2]) if eval.strengths else "None identified"
                weaknesses_str = ", ".join(eval.weaknesses[:2]) if eval.weaknesses else "None identified"
                comments[eval.phase] = f"Strengths: {strengths_str}. Areas for improvement: {weaknesses_str}."
            
            # Calculate overall score (average of phase scores)
            overall_score = total_score / len(state.phase_evaluations) if state.phase_evaluations else 0.0
            
            # Prepare data for LLM summary
            phase_scores_str = "\n".join([
                f"- {phase.value.upper()}: {score}/3" 
                for phase, score in scorecard.items()
            ])
            
            phase_details_str = "\n".join([
                f"- {eval.phase.value.upper()}: {', '.join(eval.strengths[:2])} | Weaknesses: {', '.join(eval.weaknesses[:2])}"
                for eval in state.phase_evaluations
            ])
            
            # Get top gaps (critical and high priority)
            key_gaps = [gap for gap in state.gaps if gap.severity in ["critical", "high"]]
            key_gaps_str = "\n".join([
                f"- {gap.area} ({gap.severity}): {gap.description[:100]}..."
                for gap in key_gaps[:5]
            ])
            
            # Get top recommendations (critical and high priority)
            top_recs = [rec for rec in state.recommendations if rec.priority in ["critical", "high"]]
            top_recs_str = "\n".join([
                f"- {rec.title}: {rec.description[:100]}..."
                for rec in top_recs[:5]
            ])
            
            # Get LLM summary
            response = self.llm.invoke(
                self.prompt.format_messages(
                    phase_evaluations=phase_scores_str,
                    compliance_score=state.spec_compliance.overall_compliance_score,
                    gaps_summary=key_gaps_str,
                    top_recommendations=top_recs_str,
                    document_type=doc.document_type.value if doc else "unknown",
                    document_purpose=doc.metadata.get("document_purpose", "unknown") if doc else "unknown"
                )
            )
            
            # Parse LLM response
            from ..utils.json_parser import parse_llm_json_response, create_scoring_fallback
            
            try:
                summary_data = parse_llm_json_response(response.content, create_scoring_fallback())
            except ValueError:
                summary_data = create_scoring_fallback()
            
            # Create final evaluation result
            evaluation_result = EvaluationResult(
                scorecard=scorecard,
                comments=comments,
                phase_evaluations=state.phase_evaluations,
                spec_compliance=state.spec_compliance,
                gaps=state.gaps,
                recommendations=state.recommendations,
                overall_score=overall_score,
                summary=summary_data.get("scoring_rationale", "")
            )
            
            return {
                "evaluation_result": evaluation_result,
                "summary_data": summary_data
            }
            
        except Exception as e:
            return {"error": f"Error in ScoringNode agent: {str(e)}"}


def scoring_node(state: GraphState) -> Dict[str, Any]:
    """LangGraph node function for final scoring and summary."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = ScoringNodeAgent(llm)
    
    result = agent(state)
    
    if "error" in result:
        return {"error": result["error"]}
    else:
        updates = {"evaluation_result": result["evaluation_result"]}
        
        # Store additional summary data
        if state.parsed_document:
            summary_data = result.get("summary_data", {})
            new_metadata = state.parsed_document.metadata.copy()
            new_metadata.update({
                "final_summary": summary_data.get("scoring_rationale", ""),
                "key_strengths": [],
                "critical_areas": [],
                "strategic_insights": "",
                "readiness_level": ""
            })
            
            # Create new ParsedDocument with updated metadata
            from src.models.evaluation import ParsedDocument
            updates["parsed_document"] = ParsedDocument(
                content=state.parsed_document.content,
                document_type=state.parsed_document.document_type,
                sections=state.parsed_document.sections,
                metadata=new_metadata
            )
        
        return updates 