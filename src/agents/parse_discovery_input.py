"""
Discovery Input Parser Agent

This agent handles parsing and normalizing discovery input data from various sources
including JSON, text, and manual entry formats.
"""

import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.proposal_generation import ProposalState
from ..utils.json_parser import parse_llm_json_response


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def parse_discovery_input(state: ProposalState) -> Dict[str, Any]:
    """
    Parse and normalize discovery input data from various sources.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with parsed workload classification data
    """
    try:
        discovery_input = state.discovery_input
        
        if discovery_input.source_type == "json":
            if isinstance(discovery_input.raw_data, str):
                parsed_data = json.loads(discovery_input.raw_data)
            else:
                parsed_data = discovery_input.raw_data
        else:
            # Default text parsing using LLM
            parsed_data = _parse_text_input(str(discovery_input.raw_data))
        
        return {
            "workload_classification": parsed_data
        }
        
    except Exception as e:
        return {
            "errors": [f"Input parsing failed: {str(e)}"]
        }


def _parse_text_input(raw_data: str) -> Dict[str, Any]:
    """Parse text input using LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at extracting structured information from discovery documents.

Analyze the provided text and extract:
- Applications and their details
- Technology stacks
- Business requirements
- Infrastructure information
- Dependencies and relationships

Return the information as structured JSON that can be used for migration planning.

Focus on identifying:
1. Individual applications/workloads
2. Technology components (languages, frameworks, databases)
3. Business criticality and requirements
4. Current hosting environment
5. Dependencies between systems

Return JSON format:
{
  "applications": [...],
  "infrastructure": {...},
  "business_requirements": {...}
}"""),
        ("user", "Extract structured information from this discovery text:\n\n{text}")
    ])
    
    response = llm.invoke(prompt.format_messages(text=raw_data))
    return parse_llm_json_response(
        response.content, 
        fallback_data={"source": "text", "content": raw_data}
    ) 