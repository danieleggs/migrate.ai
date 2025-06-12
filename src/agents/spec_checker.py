"""
Specification Checker Agent

Agent responsible for checking overall compliance with migrate.ai specification.
"""

from typing import Dict, Any, List
import yaml
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import GraphState, SpecCompliance
from ..utils.json_parser import parse_llm_json_response


class SpecChecker:
    """Checks overall compliance with the migrate.ai specification."""
    
    def __init__(self):
        self.spec = self._load_spec()
    
    def _load_spec(self) -> Dict[str, Any]:
        """Load the migrate.ai specification."""
        spec_path = Path(__file__).parent.parent / "config" / "modernize_ai_spec.yaml"
        with open(spec_path, 'r') as f:
            return yaml.safe_load(f)
    
    def check_compliance(self, content: str, phase_evaluations: list = None) -> SpecCompliance:
        """Check overall compliance with the specification."""
        
        core_principles = self.spec["migrate_ai_specification"]["core_principles"]
        red_flags = self.spec["migrate_ai_specification"]["red_flags"]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a migrate.ai compliance expert. Your task is to assess overall compliance with the migrate.ai Agent-Led Migration Specification.

Core Principles to evaluate:
{self._format_principles(core_principles)}

Red Flags to check for:
{self._format_red_flags(red_flags)}

Evaluation criteria:
1. Adherence to core principles
2. Absence of red flag indicators
3. Quality of technical approach
4. Overall alignment with migrate.ai approach
5. Evidence of automation and AI integration

Please provide:
1. Overall compliance score (0.0-1.0)
2. Missing elements that should be addressed
3. Compliance strengths identified
4. Areas needing improvement
5. Specific recommendations for better alignment

Return your response as JSON with this structure:
{{
    "overall_compliance_score": <number between 0.0 and 1.0>,
    "missing_elements": [<list of strings>],
    "compliance_strengths": [<list of strings>],
    "improvement_areas": [<list of strings>],
    "recommendations": [<list of strings>]
}}

Please assess compliance with migrate.ai specification and provide:
- Detailed analysis of alignment with core principles
- Identification of any red flags present
- Specific recommendations for improvement
- Overall compliance assessment"""),
            ("user", f"Evaluate this proposal content for migrate.ai specification compliance:\n\n{content}")
        ])
        
        response = llm.invoke(prompt.format_messages())
        
        # Parse the JSON response
        try:
            result = parse_llm_json_response(
                response.content,
                fallback_data={
                    "overall_compliance_score": 0.5,
                    "missing_elements": ["Could not parse compliance response"],
                    "compliance_strengths": ["Content provided for evaluation"],
                    "improvement_areas": ["Response parsing failed"],
                    "recommendations": ["Please review the content format and try again"]
                }
            )
            
            return SpecCompliance(
                overall_compliance_score=result.get("overall_compliance_score", 0.5),
                missing_elements=result.get("missing_elements", []),
                compliance_strengths=result.get("compliance_strengths", []),
                improvement_areas=result.get("improvement_areas", []),
                recommendations=result.get("recommendations", [])
            )
        except Exception as e:
            # Fallback if parsing fails
            return SpecCompliance(
                overall_compliance_score=0.5,
                missing_elements=[f"Could not parse compliance response: {str(e)}"],
                compliance_strengths=["Content provided for evaluation"],
                improvement_areas=["Response parsing failed"],
                recommendations=["Please review the content format and try again"]
            )
    
    def _format_principles(self, principles: list) -> str:
        """Format core principles for the prompt."""
        return "\n".join([f"- {principle}" for principle in principles])
    
    def _format_red_flags(self, red_flags: list) -> str:
        """Format red flags for the prompt."""
        return "\n".join([f"- {flag}" for flag in red_flags])


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def spec_checker_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node function for specification checking."""
    try:
        checker = SpecChecker()
        
        # Get the document content
        content = state.get("document_content", "")
        phase_evaluations = state.get("phase_evaluations", [])
        
        if not content:
            return {
                "errors": ["No document content available for specification checking"]
            }
        
        # Check compliance
        compliance = checker.check_compliance(content, phase_evaluations)
        
        return {
            "spec_compliance": compliance
        }
        
    except Exception as e:
        return {
            "errors": [f"Specification checking failed: {str(e)}"]
        } 