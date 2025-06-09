import json
import re
from typing import Dict, Any, Optional


def parse_llm_json_response(response_content: str, fallback_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Robustly parse JSON from LLM response content.
    
    Args:
        response_content: The raw response content from the LLM
        fallback_data: Optional fallback data to return if parsing fails
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        ValueError: If parsing fails and no fallback data is provided
    """
    # First, try direct JSON parsing
    try:
        return json.loads(response_content)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    try:
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
    except json.JSONDecodeError:
        pass
    
    # Try to find any JSON-like structure in the response
    try:
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except json.JSONDecodeError:
        pass
    
    # If all parsing attempts fail, use fallback data or raise error
    if fallback_data is not None:
        return fallback_data
    else:
        raise ValueError(f"Could not parse JSON from LLM response: {response_content[:200]}...")


def create_evaluation_fallback(phase_name: str = "unknown") -> Dict[str, Any]:
    """Create fallback evaluation data when JSON parsing fails."""
    return {
        "score": 0,
        "strengths": [f"Document structure present for {phase_name}"],
        "weaknesses": ["Unable to perform detailed evaluation due to parsing error"],
        "recommendations": ["Retry evaluation with clearer document structure"],
        "detailed_analysis": f"Fallback analysis for {phase_name} - LLM response could not be parsed"
    }


def create_compliance_fallback() -> Dict[str, Any]:
    """Create fallback compliance data when JSON parsing fails."""
    return {
        "compliant_areas": ["Document structure present"],
        "non_compliant_areas": ["Unable to perform detailed compliance analysis"],
        "missing_elements": ["Detailed compliance assessment"],
        "overall_compliance_score": 0.5,
        "red_flags_identified": ["Analysis incomplete due to parsing error"],
        "detailed_compliance_analysis": "Fallback analysis - LLM response could not be parsed"
    }


def create_gap_analysis_fallback() -> Dict[str, Any]:
    """Create fallback gap analysis data when JSON parsing fails."""
    return {
        "gaps": [
            {
                "category": "Analysis",
                "description": "Unable to perform detailed gap analysis",
                "severity": "medium",
                "impact": "Limited evaluation capability",
                "recommendation": "Retry with clearer document structure"
            }
        ],
        "summary": "Gap analysis incomplete due to parsing error"
    }


def create_recommendations_fallback() -> Dict[str, Any]:
    """Create fallback recommendations data when JSON parsing fails."""
    return {
        "recommendations": [
            {
                "category": "Document Quality",
                "priority": "medium",
                "description": "Improve document structure for better analysis",
                "rationale": "Current document could not be fully analyzed",
                "implementation_effort": "low"
            }
        ],
        "summary": "Recommendations limited due to parsing error"
    }


def create_scoring_fallback() -> Dict[str, Any]:
    """Create fallback scoring data when JSON parsing fails."""
    return {
        "overall_score": 1.0,
        "category_scores": {
            "strategic_alignment": 1.0,
            "technical_approach": 1.0,
            "risk_management": 1.0,
            "innovation": 1.0
        },
        "score_rationale": "Fallback scoring due to parsing error",
        "improvement_areas": ["Document structure and clarity"]
    } 