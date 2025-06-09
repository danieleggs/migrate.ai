from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import GraphState, Recommendation, MigrationPhase
from ..utils.json_parser import parse_llm_json_response, create_recommendations_fallback


class RecommendationsGeneratorAgent:
    """Agent responsible for generating actionable recommendations to improve Modernize.AI alignment."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Modernize.AI consultant expert. Your task is to generate specific, actionable recommendations to improve the proposal's alignment with Modernize.AI Agent-Led Migration Specification.

Focus on:
1. Addressing identified gaps and weaknesses
2. Enhancing compliance with Modernize.AI principles
3. Improving phase-specific approaches
4. Adding missing GenAI/automation elements
5. Strengthening risk mitigation and fallback planning

Prioritize recommendations by:
- CRITICAL: Essential for project success and Modernize.AI alignment
- HIGH: Important improvements that significantly enhance alignment
- MEDIUM: Valuable improvements that strengthen the approach
- LOW: Nice-to-have improvements for optimization

Make recommendations specific, actionable, and implementable."""),
            ("human", """EVALUATION CONTEXT:
{evaluation_context}

IDENTIFIED GAPS:
{gaps}

SPEC COMPLIANCE STATUS:
{compliance_status}

Please generate actionable recommendations to improve alignment with Modernize.AI specification.

Focus on:
1. Addressing identified gaps in the three migration stages
2. Enhancing GenAI and automation usage
3. Strengthening dual-track migration approach
4. Improving team capability development
5. Enhancing cost optimisation strategies
6. Strengthening security and compliance measures

For each recommendation, provide:
- Clear, actionable title
- Detailed description with specific steps
- Priority level (low/medium/high/critical)
- Associated migration stage (if applicable)
- Implementation effort estimate (low/medium/high)

Respond in JSON format:
{{
    "recommendations": [
        {{
            "title": "recommendation title",
            "description": "detailed actionable description",
            "priority": "low|medium|high|critical",
            "phase": "strategise_and_plan|migrate_and_modernise|manage_and_optimise|null",
            "implementation_effort": "low|medium|high"
        }}
    ],
    "summary": "overall recommendations summary"
}}""")
        ])
    
    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """Generate recommendations for improvement."""
        try:
            if not state.gaps or not state.spec_compliance:
                return {"error": "Missing gap analysis or compliance data for recommendations"}
            
            doc = state.parsed_document
            
            # Prepare phase evaluations summary
            phase_eval_summary = []
            for eval in state.phase_evaluations:
                phase_eval_summary.append(
                    f"- {eval.phase.value.upper()}: Score {eval.score}/3\n"
                    f"  Key Weaknesses: {', '.join(eval.weaknesses[:3])}"
                )
            
            # Prepare gaps summary
            gaps_summary = []
            for gap in state.gaps:
                phase_str = gap.phase.value if gap.phase else "general"
                gaps_summary.append(
                    f"- {gap.area} ({gap.severity}, {phase_str}): {gap.description}"
                )
            
            # Get priority gaps from metadata
            priority_gaps = doc.metadata.get("priority_gaps", []) if doc else []
            
            # Get LLM recommendations
            response = self.llm.invoke(
                self.prompt.format_messages(
                    evaluation_context="\n".join(phase_eval_summary),
                    gaps="\n".join(gaps_summary[:10]),  # Limit to top 10 gaps
                    compliance_status=", ".join(state.spec_compliance.non_compliant_areas) + " (Non-Compliant Areas), " + ", ".join(state.spec_compliance.missing_elements) + " (Missing Elements), " + f"Overall Compliance Score: {state.spec_compliance.overall_compliance_score}"
                )
            )
            
            # Parse LLM response
            try:
                analysis = parse_llm_json_response(response.content, create_recommendations_fallback())
            except ValueError:
                analysis = create_recommendations_fallback()
            
            # Convert to Recommendation objects
            recommendations = []
            for rec_data in analysis.get("recommendations", []):
                try:
                    recommendation = Recommendation(
                        title=rec_data["title"],
                        description=rec_data["description"],
                        priority=rec_data["priority"],
                        phase=rec_data["phase"],
                        implementation_effort=rec_data["implementation_effort"]
                    )
                    recommendations.append(recommendation)
                except (KeyError, ValueError) as e:
                    # Skip invalid recommendation entries
                    continue
            
            return {
                "recommendations": recommendations,
                "summary": analysis.get("summary", "No summary provided")
            }
            
        except Exception as e:
            return {"error": f"Error in RecommendationsGenerator agent: {str(e)}"}


def recommendations_generator_node(state: GraphState) -> Dict[str, Any]:
    """LangGraph node function for generating recommendations."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = RecommendationsGeneratorAgent(llm)
    
    result = agent(state)
    
    if "error" in result:
        return {"error": result["error"]}
    else:
        updates = {"recommendations": result["recommendations"]}
        
        # Store additional analysis data if needed
        if state.parsed_document:
            # Create new metadata dict with additional data
            new_metadata = state.parsed_document.metadata.copy()
            new_metadata["summary"] = result.get("summary", "")
            
            # Create new ParsedDocument with updated metadata
            from src.models.evaluation import ParsedDocument
            updates["parsed_document"] = ParsedDocument(
                content=state.parsed_document.content,
                document_type=state.parsed_document.document_type,
                sections=state.parsed_document.sections,
                metadata=new_metadata
            )
        
        return updates 