from typing import Dict, Any, List
import yaml
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import GraphState, SpecCompliance


class SpecCheckerAgent:
    """Agent responsible for checking overall compliance with Modernize.AI specification."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.spec = self._load_specification()
        self.prompt = self._create_prompt()
    
    def _load_specification(self) -> Dict[str, Any]:
        """Load the Modernize.AI specification."""
        spec_path = Path(__file__).parent.parent / "config" / "modernize_ai_spec.yaml"
        with open(spec_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create compliance checking prompt."""
        core_principles = self.spec["modernize_ai_specification"]["core_principles"]
        red_flags = self.spec["modernize_ai_specification"]["red_flags"]
        
        return ChatPromptTemplate.from_messages([
            ("system", f"""You are a Modernize.AI compliance expert. Your task is to assess overall compliance with the Modernize.AI Agent-Led Migration Specification.

CORE PRINCIPLES TO CHECK:
{yaml.dump(core_principles, default_flow_style=False)}

RED FLAGS TO IDENTIFY:
{yaml.dump(red_flags, default_flow_style=False)}

Assess the document for:
1. Adherence to core principles
2. Presence of red flags
3. Missing critical elements
4. Overall alignment with Modernize.AI approach

Be thorough and specific in your analysis."""),
            ("human", """DOCUMENT CONTENT AND ANALYSIS:

Document Type: {document_type}
Document Purpose: {document_purpose}

Phase Evaluations Summary:
{phase_evaluations}

Key Themes: {key_themes}
Migration Indicators: {migration_indicators}

Full Content Sample:
{content_sample}

Please assess compliance with Modernize.AI specification and provide:

1. Areas where the document is compliant
2. Areas where the document is non-compliant
3. Missing elements that should be present
4. Overall compliance score (0.0-1.0)
5. Specific red flags identified

IMPORTANT: Respond with ONLY valid JSON in the exact format below. Do not include any markdown formatting, explanations, or additional text.

{{
    "compliant_areas": ["area1", "area2"],
    "non_compliant_areas": ["area1", "area2"],
    "missing_elements": ["element1", "element2"],
    "overall_compliance_score": 0.7,
    "red_flags_identified": ["flag1", "flag2"],
    "detailed_compliance_analysis": "comprehensive analysis"
}}""")
        ])
    
    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """Check specification compliance."""
        try:
            if not state.parsed_document:
                return {"error": "No parsed document found in state"}
            
            doc = state.parsed_document
            
            # Prepare phase evaluations summary
            phase_eval_summary = []
            for eval in state.phase_evaluations:
                phase_eval_summary.append(
                    f"- {eval.phase.value}: Score {eval.score}/3, "
                    f"Strengths: {', '.join(eval.strengths[:2])}, "
                    f"Weaknesses: {', '.join(eval.weaknesses[:2])}"
                )
            
            # Get LLM compliance analysis
            response = self.llm.invoke(
                self.prompt.format_messages(
                    document_type=doc.document_type.value,
                    document_purpose=doc.metadata.get("document_purpose", "Unknown"),
                    phase_evaluations="\n".join(phase_eval_summary),
                    key_themes=", ".join(doc.metadata.get("key_themes", [])),
                    migration_indicators=", ".join(doc.metadata.get("migration_indicators", [])),
                    content_sample=doc.content[:2000]
                )
            )
            
            # Parse LLM response
            from ..utils.json_parser import parse_llm_json_response, create_compliance_fallback
            
            try:
                analysis = parse_llm_json_response(response.content, create_compliance_fallback())
            except ValueError:
                # This shouldn't happen since we provide fallback data, but just in case
                analysis = create_compliance_fallback()
            
            # Create SpecCompliance object
            spec_compliance = SpecCompliance(
                compliant_areas=analysis.get("compliant_areas", []),
                non_compliant_areas=analysis.get("non_compliant_areas", []),
                missing_elements=analysis.get("missing_elements", []),
                overall_compliance_score=float(analysis.get("overall_compliance_score", 0.0))
            )
            
            return {
                "spec_compliance": spec_compliance,
                "red_flags_identified": analysis.get("red_flags_identified", []),
                "detailed_analysis": analysis.get("detailed_compliance_analysis", "")
            }
            
        except Exception as e:
            return {"error": f"Error in SpecChecker agent: {str(e)}"}


def spec_checker_node(state: GraphState) -> Dict[str, Any]:
    """LangGraph node function for specification compliance checking."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = SpecCheckerAgent(llm)
    
    result = agent(state)
    
    if "error" in result:
        return {"error": result["error"]}
    else:
        updates = {"spec_compliance": result["spec_compliance"]}
        
        # Store additional analysis data if needed
        if state.parsed_document:
            # Create new metadata dict with additional data
            new_metadata = state.parsed_document.metadata.copy()
            new_metadata["red_flags"] = result.get("red_flags_identified", [])
            new_metadata["compliance_analysis"] = result.get("detailed_analysis", "")
            
            # Create new ParsedDocument with updated metadata
            from src.models.evaluation import ParsedDocument
            updates["parsed_document"] = ParsedDocument(
                content=state.parsed_document.content,
                document_type=state.parsed_document.document_type,
                sections=state.parsed_document.sections,
                metadata=new_metadata
            )
        
        return updates 