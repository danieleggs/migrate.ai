"""
Wave Planner Agent

This agent handles migration wave planning using dual-track methodology
for organizing applications into logical migration phases.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.proposal_generation import ProposalState, WaveGroup, WorkloadComplexity
from ..utils.json_parser import parse_llm_json_response


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def plan_migration_waves(state: ProposalState) -> Dict[str, Any]:
    """
    Plan migration waves using dual-track methodology.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with migration wave planning data
    """
    try:
        classified_workloads = state.classified_workloads
        
        if not classified_workloads:
            return {"errors": ["No classified workloads available for wave planning"]}
        
        # Generate wave plan using LLM
        wave_plan = _generate_wave_plan(classified_workloads)
        
        return {
            "migration_waves": wave_plan
        }
        
    except Exception as e:
        return {
            "errors": [f"Wave planning failed: {str(e)}"]
        }


def _generate_wave_plan(classified_workloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate migration wave plan using LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert cloud migration strategist specializing in wave planning using dual-track methodology.

Analyze the classified workloads and create a migration wave plan that follows these principles:

**Dual-Track Approach:**
- **Track 1 (Foundation)**: Infrastructure, shared services, and foundational components
- **Track 2 (Applications)**: Business applications that depend on Track 1 components

**Wave Planning Criteria:**
1. **Dependencies**: Applications with fewer dependencies go first
2. **Complexity**: Start with simpler applications to build confidence
3. **Business Criticality**: Balance risk - not all critical apps in one wave
4. **Resource Capacity**: Distribute effort evenly across waves
5. **Learning Curve**: Early wins to build team expertise

**Wave Structure:**
- Wave 0: Proof of Concept (1-2 simple applications)
- Wave 1-N: Production migrations (3-5 applications per wave)

For each wave, provide:
- Applications included
- Track assignment (Foundation/Application)
- Dependencies satisfied
- Estimated timeline
- Risk level
- Success criteria

Return JSON format:
{
  "methodology": "Dual-Track Migration",
  "total_waves": number,
  "estimated_duration_months": number,
  "waves": [
    {
      "wave_number": 0,
      "name": "Wave Name",
      "track": "Foundation|Application|Mixed",
      "applications": ["app1", "app2"],
      "duration_weeks": number,
      "dependencies_satisfied": ["dep1", "dep2"],
      "risk_level": "Low|Medium|High",
      "success_criteria": ["criteria1", "criteria2"],
      "notes": "Additional planning notes"
    }
  ]
}"""),
        ("user", "Create a migration wave plan for these classified workloads:\n\n{workloads}")
    ])
    
    workloads_str = str(classified_workloads)
    response = llm.invoke(prompt.format_messages(workloads=workloads_str))
    
    wave_plan = parse_llm_json_response(
        response.content,
        fallback_data={
            "methodology": "Dual-Track Migration",
            "total_waves": 1,
            "estimated_duration_months": 6,
            "waves": [{
                "wave_number": 1,
                "name": "Initial Migration Wave",
                "track": "Mixed",
                "applications": [app.get("name", "Unknown") for app in classified_workloads[:3]],
                "duration_weeks": 8,
                "risk_level": "Medium",
                "success_criteria": ["Applications migrated successfully"]
            }]
        }
    )
    
    return wave_plan


def validate_wave_plan(wave_groups: List[WaveGroup], applications: List) -> List[str]:
    """
    Validate the wave plan for consistency and completeness.
    
    Args:
        wave_groups: List of planned waves
        applications: List of all applications
        
    Returns:
        List of validation warnings
    """
    warnings = []
    
    if not wave_groups:
        warnings.append("No migration waves were planned")
        return warnings
    
    # Check all applications are included
    all_wave_apps = set()
    for wave in wave_groups:
        all_wave_apps.update(wave.applications)
    
    app_names = {app.name for app in applications}
    missing_apps = app_names - all_wave_apps
    if missing_apps:
        warnings.append(f"Applications not included in any wave: {', '.join(missing_apps)}")
    
    extra_apps = all_wave_apps - app_names
    if extra_apps:
        warnings.append(f"Wave plan includes unknown applications: {', '.join(extra_apps)}")
    
    # Check wave dependencies
    for wave in wave_groups:
        for dep_wave_num in wave.dependencies:
            if not any(w.wave_number == dep_wave_num for w in wave_groups):
                warnings.append(f"Wave {wave.wave_number} depends on non-existent wave {dep_wave_num}")
            elif dep_wave_num >= wave.wave_number:
                warnings.append(f"Wave {wave.wave_number} depends on later wave {dep_wave_num}")
    
    # Check for reasonable wave sizes
    for wave in wave_groups:
        if len(wave.applications) > 10:
            warnings.append(f"Wave {wave.wave_number} has too many applications ({len(wave.applications)})")
        elif len(wave.applications) == 0:
            warnings.append(f"Wave {wave.wave_number} has no applications")
    
    return warnings


def optimize_wave_sequence(wave_groups: List[WaveGroup]) -> List[WaveGroup]:
    """
    Optimize the wave sequence based on dependencies and risk levels.
    
    Args:
        wave_groups: List of wave groups to optimize
        
    Returns:
        Optimized list of wave groups
    """
    # Sort waves by wave number to ensure proper sequence
    sorted_waves = sorted(wave_groups, key=lambda w: w.wave_number)
    
    # Validate dependency order
    for i, wave in enumerate(sorted_waves):
        for dep_wave_num in wave.dependencies:
            if dep_wave_num >= wave.wave_number:
                # Move dependent wave later
                wave.wave_number = dep_wave_num + 1
                # Update subsequent waves
                for j in range(i + 1, len(sorted_waves)):
                    if sorted_waves[j].wave_number <= wave.wave_number:
                        sorted_waves[j].wave_number = wave.wave_number + (j - i)
    
    return sorted(sorted_waves, key=lambda w: w.wave_number)


def calculate_wave_metrics(wave_groups: List[WaveGroup]) -> Dict[str, Any]:
    """
    Calculate metrics for the wave plan.
    
    Args:
        wave_groups: List of wave groups
        
    Returns:
        Dictionary with wave plan metrics
    """
    if not wave_groups:
        return {}
    
    total_duration = sum(wave.estimated_duration_weeks for wave in wave_groups)
    total_applications = sum(len(wave.applications) for wave in wave_groups)
    
    risk_distribution = {}
    for wave in wave_groups:
        risk_level = wave.risk_level.value
        risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
    
    return {
        "total_waves": len(wave_groups),
        "total_duration_weeks": total_duration,
        "total_applications": total_applications,
        "average_apps_per_wave": total_applications / len(wave_groups),
        "risk_distribution": risk_distribution,
        "parallel_execution_possible": any(
            len(wave.dependencies) == 0 for wave in wave_groups[1:]
        )
    } 