from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import GraphState, Gap, MigrationPhase


class GapHighlighterAgent:
    """Agent responsible for identifying gaps and weaknesses in the proposal."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Modernize.AI gap analysis expert. Your task is to identify specific gaps and weaknesses in the proposal based on the phase evaluations and specification compliance analysis.

Focus on identifying:
1. Missing or inadequate elements in each migration stage
2. Gaps in GenAI and automation implementation
3. Weaknesses in dual-track migration approach
4. Missing team capability development plans
5. Inadequate cost optimization strategies
6. Security and compliance gaps
7. Risk mitigation shortcomings

For each gap, provide:
- Clear description of what's missing or inadequate
- Severity level (low/medium/high/critical)
- Associated migration stage (if applicable)
- Impact on project success
- Specific evidence from the evaluation

Be specific and actionable in your gap identification."""),
            ("human", """EVALUATION RESULTS:

Phase Evaluations:
{phase_evaluations}

Specification Compliance:
{spec_compliance}

Document Analysis:
{document_analysis}

Based on this evaluation data, identify specific gaps and weaknesses in the proposal.

For each gap identified, provide:
- Area/category of the gap
- Detailed description of what's missing or inadequate
- Severity level (low/medium/high/critical)
- Associated migration stage (strategise_and_plan/migrate_and_modernise/manage_and_optimise/null)
- Impact description
- Evidence from the evaluation supporting this gap

Respond in JSON format:
{{
    "gaps": [
        {{
            "area": "gap category",
            "description": "detailed description of the gap",
            "severity": "low|medium|high|critical",
            "phase": "strategise_and_plan|migrate_and_modernise|manage_and_optimise|null",
            "impact": "description of impact on project success",
            "evidence": "specific evidence from evaluation"
        }}
    ],
    "summary": "overall gap analysis summary"
}}""")
        ])
    
    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """Identify gaps in the proposal."""
        try:
            if not state.spec_compliance or not state.phase_evaluations:
                return {"error": "Missing evaluation data for gap analysis"}
            
            doc = state.parsed_document
            
            # Prepare phase evaluations summary
            phase_eval_details = []
            for eval in state.phase_evaluations:
                phase_eval_details.append(
                    f"- {eval.phase.value.upper()}: Score {eval.score}/3\n"
                    f"  Strengths: {', '.join(eval.strengths)}\n"
                    f"  Weaknesses: {', '.join(eval.weaknesses)}\n"
                    f"  Evidence: {', '.join(eval.evidence)}"
                )
            
            # Get red flags from metadata
            red_flags = doc.metadata.get("red_flags", []) if doc else []
            
            # Get LLM gap analysis
            response = self.llm.invoke(
                self.prompt.format_messages(
                    phase_evaluations="\n\n".join(phase_eval_details),
                    spec_compliance=", ".join(state.spec_compliance.compliant_areas) + " (Compliant), " + ", ".join(state.spec_compliance.non_compliant_areas) + " (Non-Compliant)",
                    document_analysis=", ".join(red_flags),
                    document_type=doc.document_type.value if doc else "unknown",
                    document_purpose=doc.metadata.get("document_purpose", "unknown") if doc else "unknown",
                    key_themes=", ".join(doc.metadata.get("key_themes", [])) if doc else "none"
                )
            )
            
            # Parse LLM response
            from ..utils.json_parser import parse_llm_json_response, create_gap_analysis_fallback
            
            try:
                analysis = parse_llm_json_response(response.content, create_gap_analysis_fallback())
            except ValueError:
                analysis = create_gap_analysis_fallback()
            
            # Convert to Gap objects
            gaps = []
            for gap_data in analysis.get("gaps", []):
                try:
                    # Handle phase conversion
                    phase = None
                    if gap_data.get("phase") and gap_data["phase"] != "null":
                        try:
                            phase = MigrationPhase(gap_data["phase"])
                        except ValueError:
                            phase = None
                    
                    gap = Gap(
                        area=gap_data["area"],
                        severity=gap_data["severity"],
                        description=gap_data["description"],
                        impact=gap_data["impact"],
                        phase=phase
                    )
                    gaps.append(gap)
                except (KeyError, ValueError) as e:
                    # Skip invalid gap entries
                    continue
            
            return {
                "gaps": gaps,
                "gap_summary": analysis.get("gap_summary", ""),
                "priority_gaps": analysis.get("priority_gaps", [])
            }
            
        except Exception as e:
            return {"error": f"Error in GapHighlighter agent: {str(e)}"}


def gap_highlighter_node(state: GraphState) -> Dict[str, Any]:
    """LangGraph node function for gap identification."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = GapHighlighterAgent(llm)
    
    result = agent(state)
    
    if "error" in result:
        return {"error": result["error"]}
    else:
        updates = {"gaps": result["gaps"]}
        
        # Store additional analysis data if needed
        if state.parsed_document:
            # Create new metadata dict with additional data
            new_metadata = state.parsed_document.metadata.copy()
            new_metadata["gap_summary"] = result.get("gap_summary", "")
            new_metadata["priority_gaps"] = result.get("priority_gaps", [])
            
            # Create new ParsedDocument with updated metadata
            from src.models.evaluation import ParsedDocument
            updates["parsed_document"] = ParsedDocument(
                content=state.parsed_document.content,
                document_type=state.parsed_document.document_type,
                sections=state.parsed_document.sections,
                metadata=new_metadata
            )
        
        return updates 