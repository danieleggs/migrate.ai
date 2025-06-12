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
            "discovery_input": state.discovery_input,
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
    
    # Extract discovery input context
    discovery_input = context_data.get("discovery_input")
    context_info = ""
    
    if discovery_input:
        context_info = f"""
**Client Information:**
- Client: {discovery_input.client_name}
- Project: {discovery_input.project_name}

**Business Context:**
- Business Context: {discovery_input.business_context or 'Not specified'}
"""
        
        if hasattr(discovery_input, 'business_drivers') and discovery_input.business_drivers:
            context_info += f"- Primary Drivers: {', '.join(discovery_input.business_drivers)}\n"
        
        if hasattr(discovery_input, 'target_cloud') and discovery_input.target_cloud and discovery_input.target_cloud != "Not Specified":
            context_info += f"- Target Cloud: {discovery_input.target_cloud}\n"
        
        if hasattr(discovery_input, 'migration_approach') and discovery_input.migration_approach and discovery_input.migration_approach != "Not Specified":
            context_info += f"- Migration Approach: {discovery_input.migration_approach}\n"
        
        if hasattr(discovery_input, 'timeline_constraint') and discovery_input.timeline_constraint and discovery_input.timeline_constraint != "Not Specified":
            context_info += f"- Timeline: {discovery_input.timeline_constraint}\n"
        
        if hasattr(discovery_input, 'compliance_requirements') and discovery_input.compliance_requirements:
            compliance_list = [req for req in discovery_input.compliance_requirements if req != "None"]
            if compliance_list:
                context_info += f"- Compliance: {', '.join(compliance_list)}\n"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert technical writer specializing in cloud migration proposals. 

Generate professional, comprehensive content for a migration proposal based on the provided analysis data and client context.

Create three main sections:

**1. Executive Summary**
- High-level overview of the migration initiative tailored to the client
- Key benefits and business value aligned with their drivers
- Timeline and resource overview
- Success metrics relevant to their objectives

**2. Project Overview**
- Detailed description of the migration scope for this specific client
- Current state assessment based on discovery data
- Target state vision aligned with their target cloud and approach
- Migration approach and methodology (reference dual-track agile delivery)
- Key assumptions and constraints specific to their context

**3. Scope Definition**
- Detailed breakdown of applications and workloads discovered
- In-scope and out-of-scope items
- Dependencies and prerequisites
- Success criteria and acceptance criteria aligned with business drivers

**Writing Guidelines:**
- Use the client name and project name throughout
- Reference their specific business drivers and context
- Align recommendations with their target cloud platform
- Consider their timeline constraints and compliance requirements
- Professional, clear, and concise language
- Use bullet points and structured formatting
- Include specific details from the analysis
- Focus on business value and outcomes relevant to their drivers

Return JSON format:
{{
  "executive_summary": "Executive summary content...",
  "overview": "Project overview content...",
  "scope": "Scope definition content..."
}}"""),
        ("user", f"""Generate migration proposal content based on this analysis:

{context_info}

**Technical Analysis:**
{str(context_data)}""")
    ])
    
    response = llm.invoke(prompt.format_messages())
    
    content = parse_llm_json_response(
        response.content,
        fallback_data={
            "executive_summary": f"This migration proposal outlines the strategy for {discovery_input.client_name if discovery_input else 'the client'} to modernize applications to cloud-native architecture.",
            "overview": f"The {discovery_input.project_name if discovery_input else 'migration project'} involves migrating existing applications to cloud infrastructure with modernization opportunities.",
            "scope": "The scope includes application assessment, migration planning, and implementation across multiple waves."
        }
    )
    
    return content 