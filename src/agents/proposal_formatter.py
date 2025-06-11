"""
Proposal Formatting Agent

This agent handles final formatting and assembly of proposal sections into complete documents.
"""

import os
from typing import Dict, Any, List
from datetime import datetime

from ..models.proposal_generation import ProposalState, ProposalSection


def format_proposal_sections(state: ProposalState) -> Dict[str, Any]:
    """Format all content into structured proposal sections."""
    try:
        sections = list(state.proposal_sections)  # Copy existing sections
        
        # Generate additional sections
        if state.wave_groups:
            wave_content = _generate_wave_planning_content(state)
            sections.append(ProposalSection(
                section_number="3",
                title="Wave Group Planning",
                content=wave_content
            ))
        
        if state.migration_strategies:
            strategy_content = _generate_strategy_content(state)
            sections.append(ProposalSection(
                section_number="4",
                title="6 R's Classification & Migration Strategy",
                content=strategy_content
            ))
        
        if state.architecture_recommendations:
            architecture_content = _generate_architecture_content(state)
            sections.append(ProposalSection(
                section_number="5",
                title="Cloud Architecture & Best Practices",
                content=architecture_content
            ))
        
        if state.genai_tool_plans:
            genai_content = _generate_genai_content(state)
            sections.append(ProposalSection(
                section_number="6",
                title="GenAI Tooling and Automation Plan",
                content=genai_content
            ))
        
        if state.sprint_estimates:
            timeline_content = _generate_timeline_content(state)
            sections.append(ProposalSection(
                section_number="7",
                title="Sprint Timeline and Effort Estimate",
                content=timeline_content
            ))
        
        # Combine all sections into markdown
        markdown_output = _combine_sections_to_markdown(sections, state)
        
        return {
            "proposal_sections": sections,
            "markdown_output": markdown_output
        }
        
    except Exception as e:
        return {
            "errors": [f"Template formatting failed: {str(e)}"]
        }


def create_output_files(state: ProposalState) -> Dict[str, Any]:
    """Create final output files from formatted content."""
    try:
        # Create output directory
        output_dir = "outputs/proposals"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_name = state.discovery_input.client_name.replace(" ", "_").lower()
        
        markdown_path = f"{output_dir}/{client_name}_proposal_{timestamp}.md"
        docx_path = f"{output_dir}/{client_name}_proposal_{timestamp}.docx"
        pdf_path = f"{output_dir}/{client_name}_proposal_{timestamp}.pdf"
        
        # Save markdown
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(state.markdown_output)
        
        # Create placeholder files for DOCX and PDF
        with open(docx_path.replace('.docx', '_placeholder.txt'), 'w') as f:
            f.write("DOCX conversion placeholder\n\n")
            f.write(state.markdown_output)
        
        with open(pdf_path.replace('.pdf', '_placeholder.txt'), 'w') as f:
            f.write("PDF conversion placeholder\n\n")
            f.write(state.markdown_output)
        
        return {
            "docx_path": docx_path,
            "pdf_path": pdf_path
        }
        
    except Exception as e:
        return {
            "errors": [f"Output file creation failed: {str(e)}"]
        }


def _generate_wave_planning_content(state: ProposalState) -> str:
    """Generate wave planning section content."""
    content = "## Migration Wave Strategy\n\n"
    content += "The migration will be executed in carefully planned waves to minimize risk and ensure business continuity.\n\n"
    
    for wave in state.wave_groups:
        content += f"### Wave {wave.wave_number}: {wave.name}\n\n"
        content += f"**Strategy:** {wave.strategy}\n"
        content += f"**Duration:** {wave.estimated_duration_weeks} weeks\n"
        content += f"**Risk Level:** {wave.risk_level.value}\n\n"
        content += f"**Applications:**\n"
        for app in wave.applications:
            content += f"- {app}\n"
        content += "\n"
    
    return content


def _generate_strategy_content(state: ProposalState) -> str:
    """Generate 6R strategy section content."""
    content = "## Migration Strategy Classification\n\n"
    content += "Each application has been classified using the 6 R's migration strategy framework:\n\n"
    
    # Group by strategy
    strategy_groups = {}
    for app_name, strategy in state.migration_strategies.items():
        if strategy not in strategy_groups:
            strategy_groups[strategy] = []
        strategy_groups[strategy].append(app_name)
    
    for strategy, apps in strategy_groups.items():
        content += f"### {strategy.value.title()}\n\n"
        for app in apps:
            content += f"- {app}\n"
        content += "\n"
    
    return content


def _generate_architecture_content(state: ProposalState) -> str:
    """Generate architecture section content."""
    content = "## Cloud Architecture Recommendations\n\n"
    
    for rec in state.architecture_recommendations:
        content += f"### {rec.cloud_provider.value.upper()} Architecture\n\n"
        content += f"**Recommended Services:**\n"
        for service_type, service_name in rec.services.items():
            content += f"- {service_type.title()}: {service_name}\n"
        content += "\n"
        
        content += f"**Architecture Patterns:**\n"
        for pattern in rec.patterns:
            content += f"- {pattern}\n"
        content += "\n"
    
    return content


def _generate_genai_content(state: ProposalState) -> str:
    """Generate GenAI tooling section content."""
    content = "## GenAI Tooling and Automation Plan\n\n"
    content += "The following GenAI tools will accelerate the migration process:\n\n"
    
    for plan in state.genai_tool_plans:
        content += f"### {plan.tool.value.replace('_', ' ').title()}\n\n"
        content += f"**Use Cases:**\n"
        for use_case in plan.use_cases:
            content += f"- {use_case}\n"
        content += "\n"
        
        content += f"**Expected Benefits:**\n"
        for benefit in plan.expected_benefits:
            content += f"- {benefit}\n"
        content += "\n"
    
    return content


def _generate_timeline_content(state: ProposalState) -> str:
    """Generate timeline and effort section content."""
    content = "## Sprint Timeline and Effort Estimate\n\n"
    
    total_sprints = sum(estimate.total_sprints for estimate in state.sprint_estimates)
    total_weeks = total_sprints * 2  # 2-week sprints
    
    content += f"**Overall Timeline:** {total_weeks} weeks ({total_sprints} sprints)\n\n"
    
    for estimate in state.sprint_estimates:
        wave = next((w for w in state.wave_groups if w.wave_number == estimate.wave_number), None)
        if wave:
            content += f"### Wave {estimate.wave_number}: {wave.name}\n\n"
            content += f"**Duration:** {estimate.total_sprints} sprints ({estimate.total_sprints * 2} weeks)\n"
            content += f"**Team Size:** {estimate.team_size} people\n\n"
            
            content += f"**Effort Breakdown:**\n"
            for activity, sprints in estimate.effort_breakdown.items():
                content += f"- {activity.title()}: {sprints} sprints\n"
            content += "\n"
    
    return content


def _combine_sections_to_markdown(sections: List[ProposalSection], state: ProposalState) -> str:
    """Combine all sections into a complete markdown document."""
    markdown = f"# Migration Proposal: {state.discovery_input.project_name}\n\n"
    markdown += f"**Client:** {state.discovery_input.client_name}\n"
    markdown += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    markdown += "---\n\n"
    
    for section in sorted(sections, key=lambda x: x.section_number):
        markdown += f"# {section.section_number}. {section.title}\n\n"
        markdown += section.content + "\n\n"
        markdown += "---\n\n"
    
    return markdown 