"""
Content Generator Agent

This agent handles generation of overview and scope sections
for migration proposals based on analyzed data.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.proposal_generation import ProposalState
from ..utils.json_parser import parse_llm_json_response


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def generate_overview_and_scope(state: ProposalState) -> Dict[str, Any]:
    """
    Generate overview and scope sections for the migration proposal.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with generated content sections
    """
    try:
        # Gather all available data for content generation
        context_data = {
            "workload_classification": state.workload_classification,
            "classified_workloads": state.classified_workloads,
            "migration_waves": state.migration_waves,
            "migration_strategies": state.migration_strategies
        }
        
        # Generate overview and scope content
        content = _generate_content_sections(context_data)
        
        return {
            "overview_content": content.get("overview", ""),
            "scope_content": content.get("scope", ""),
            "executive_summary": content.get("executive_summary", "")
        }
        
    except Exception as e:
        return {
            "errors": [f"Content generation failed: {str(e)}"]
        }


def _generate_content_sections(context_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate overview and scope content using LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert technical writer specializing in cloud migration proposals. 

Generate professional, comprehensive content for a migration proposal based on the provided analysis data.

Create three main sections:

**1. Executive Summary**
- High-level overview of the migration initiative
- Key benefits and business value
- Timeline and resource overview
- Success metrics

**2. Project Overview**
- Detailed description of the migration scope
- Current state assessment
- Target state vision
- Migration approach and methodology
- Key assumptions and constraints

**3. Scope Definition**
- Detailed breakdown of applications and workloads
- In-scope and out-of-scope items
- Dependencies and prerequisites
- Success criteria and acceptance criteria

**Writing Guidelines:**
- Professional, clear, and concise language
- Use bullet points and structured formatting
- Include specific details from the analysis
- Avoid technical jargon where possible
- Focus on business value and outcomes

Return JSON format:
{
  "executive_summary": "Executive summary content...",
  "overview": "Project overview content...",
  "scope": "Scope definition content..."
}"""),
        ("user", "Generate migration proposal content based on this analysis:\n\n{context}")
    ])
    
    context_str = str(context_data)
    response = llm.invoke(prompt.format_messages(context=context_str))
    
    content = parse_llm_json_response(
        response.content,
        fallback_data={
            "executive_summary": "This migration proposal outlines the strategy for modernizing applications to cloud-native architecture.",
            "overview": "The project involves migrating existing applications to cloud infrastructure with modernization opportunities.",
            "scope": "The scope includes application assessment, migration planning, and implementation across multiple waves."
        }
    )
    
    return content 