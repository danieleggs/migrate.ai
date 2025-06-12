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
        Dictionary with migration wave plan
    """
    try:
        classified_workloads = state.classified_workloads
        
        if not classified_workloads:
            return {"errors": ["No classified workloads available for wave planning"]}
        
        # Generate wave plan using LLM
        try:
            wave_plan = _generate_wave_plan(classified_workloads)
        except Exception as e:
            # If LLM fails, use fallback planning
            if "rate_limit" in str(e).lower() or "429" in str(e):
                print("Rate limit hit, using fallback wave planning")
                wave_plan = _create_fallback_wave_plan(classified_workloads)
            else:
                raise e
        
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
        ("system", """You are an expert cloud migration strategist specializing in dual-track agile delivery methodology.

Analyze the classified workloads and create a migration wave plan using the dual-track approach:

**Dual-Track Agile Delivery Model:**
A disciplined agile delivery model that runs two parallel, inter-locking tracks:

- **Discovery Track**: Runs one sprint ahead, investigating user needs and technical feasibility, refining and sizing backlog items, prototyping solutions, and validating them with stakeholders
- **Delivery Track**: Works from the discovery-ready backlog to build, test and release migration increments in short, time-boxed sprints, including continuous-service-improvement items

**Key Principles:**
1. **Validated-then-built workflow**: Discovery Track creates validated backlog for Delivery Track
2. **Continuous stakeholder collaboration**: Embedded throughout both tracks
3. **Reduced rework**: Validation before building minimizes rework
4. **Rapid incremental delivery**: Time-boxed sprints enable fast delivery of migrated workloads
5. **Inter-locking tracks**: Discovery stays one sprint ahead of Delivery

**Wave Planning Approach:**
- Start with discovery-ready workloads for immediate Delivery Track
- Run Discovery Track for complex workloads requiring investigation
- Maintain continuous flow between tracks
- Include continuous service improvement items
- Use 2-week sprint cycles for both tracks

For each wave, provide:
- Track type (Discovery or Delivery)
- Sprint count and duration
- Stakeholder collaboration approach
- Success criteria focused on validation or delivery

Return JSON format:
{{
  "methodology": "Dual-Track Agile Delivery",
  "methodology_description": "Discovery and Delivery tracks running in parallel",
  "total_waves": number,
  "total_sprints": number,
  "estimated_duration_months": number,
  "key_principles": ["principle1", "principle2"],
  "waves": [
    {{
      "wave_number": number,
      "name": "Wave Name",
      "track": "Discovery|Delivery",
      "track_description": "track purpose and approach",
      "applications": ["app1", "app2"],
      "duration_weeks": number,
      "sprint_count": number,
      "dependencies_satisfied": ["dep1", "dep2"],
      "risk_level": "Low|Medium|High",
      "success_criteria": ["criteria1", "criteria2"],
      "delivery_approach": "sprint methodology description",
      "stakeholder_collaboration": "collaboration approach",
      "notes": "Additional planning notes"
    }}
  ]
}}"""),
        ("user", "Create a migration wave plan for these classified workloads:\n\n{workloads}")
    ])
    
    workloads_str = str(classified_workloads)
    response = llm.invoke(prompt.format_messages(workloads=workloads_str))
    
    wave_plan = parse_llm_json_response(
        response.content,
        fallback_data={
            "methodology": "Dual-Track Agile Delivery",
            "methodology_description": "Discovery and Delivery tracks running in parallel",
            "total_waves": 2,
            "total_sprints": 6,
            "estimated_duration_months": 6,
            "key_principles": [
                "Discovery Track runs one sprint ahead",
                "Validated-then-built workflow",
                "Continuous stakeholder collaboration"
            ],
            "waves": [
                {
                    "wave_number": 1,
                    "name": "Discovery Track - Initial Investigation",
                    "track": "Discovery",
                    "track_description": "User needs investigation and technical feasibility",
                    "applications": [app.get("name", "Unknown") for app in classified_workloads[:2]],
                    "duration_weeks": 4,
                    "sprint_count": 2,
                    "risk_level": "Low",
                    "success_criteria": ["Technical feasibility validated", "Backlog items refined"],
                    "delivery_approach": "Discovery sprints with stakeholder validation",
                    "stakeholder_collaboration": "Continuous validation sessions"
                },
                {
                    "wave_number": 2,
                    "name": "Delivery Track - Initial Migration",
                    "track": "Delivery",
                    "track_description": "Building validated migration increments",
                    "applications": [app.get("name", "Unknown") for app in classified_workloads[:2]],
                    "duration_weeks": 8,
                    "sprint_count": 4,
                    "risk_level": "Medium",
                    "success_criteria": ["Migration increments delivered", "Stakeholder feedback incorporated"],
                    "delivery_approach": "Time-boxed sprints with continuous delivery",
                    "stakeholder_collaboration": "Sprint reviews and demos"
                }
            ]
        }
    )
    
    return wave_plan


def _create_fallback_wave_plan(classified_workloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a fallback wave plan using dual-track agile delivery methodology."""
    
    # Group workloads by migration readiness and complexity for dual-track planning
    discovery_ready = []  # Workloads ready for immediate delivery track
    needs_discovery = []  # Workloads requiring discovery track investigation
    
    for workload in classified_workloads:
        complexity = workload.get("complexity", "Medium").lower()
        migration_readiness = workload.get("migration_readiness", "Needs Assessment").lower()
        
        if "ready" in migration_readiness and complexity == "low":
            discovery_ready.append(workload)
        else:
            needs_discovery.append(workload)
    
    waves = []
    
    # Wave 1: Discovery-Ready Workloads (Delivery Track)
    if discovery_ready:
        waves.append({
            "wave_number": 1,
            "name": "Discovery-Ready Migration",
            "track": "Delivery",
            "track_description": "Validated workloads ready for immediate migration execution",
            "applications": [w.get("name", "Unknown") for w in discovery_ready],
            "duration_weeks": 4,
            "sprint_count": 2,
            "dependencies_satisfied": [],
            "risk_level": "Low",
            "success_criteria": [
                "Migration increments delivered in 2-week sprints",
                "Continuous stakeholder feedback incorporated",
                "Migration patterns validated and documented"
            ],
            "delivery_approach": "Time-boxed sprints with continuous delivery",
            "stakeholder_collaboration": "Weekly demos and feedback sessions",
            "notes": "Validated-then-built approach for low-risk workloads"
        })
    
    # Wave 2: Discovery Track Investigation (1 sprint ahead)
    discovery_batch_1 = needs_discovery[:len(needs_discovery)//2] if needs_discovery else []
    if discovery_batch_1:
        waves.append({
            "wave_number": 2,
            "name": "Discovery Track - Batch 1",
            "track": "Discovery",
            "track_description": "Investigation of user needs, technical feasibility, and solution prototyping",
            "applications": [w.get("name", "Unknown") for w in discovery_batch_1],
            "duration_weeks": 6,
            "sprint_count": 3,
            "dependencies_satisfied": ["Wave 1 migration patterns established"],
            "risk_level": "Medium",
            "success_criteria": [
                "User needs and technical feasibility validated",
                "Backlog items refined and sized",
                "Solution prototypes created and validated",
                "Stakeholder approval for delivery track"
            ],
            "discovery_activities": [
                "Technical feasibility assessment",
                "User needs investigation",
                "Solution prototyping",
                "Stakeholder validation sessions"
            ],
            "delivery_approach": "Discovery sprints feeding validated backlog to delivery track",
            "stakeholder_collaboration": "Continuous collaboration and validation",
            "notes": "One sprint ahead of delivery track, creating validated-ready backlog"
        })
    
    # Wave 3: Delivery Track - Batch 1 (from Discovery Track output)
    if discovery_batch_1:
        waves.append({
            "wave_number": 3,
            "name": "Delivery Track - Batch 1",
            "track": "Delivery",
            "track_description": "Building and releasing validated migration increments",
            "applications": [w.get("name", "Unknown") for w in discovery_batch_1],
            "duration_weeks": 8,
            "sprint_count": 4,
            "dependencies_satisfied": ["Discovery Track validation completed"],
            "risk_level": "Medium",
            "success_criteria": [
                "Migration increments built and tested",
                "Continuous service improvement implemented",
                "Stakeholder feedback incorporated",
                "Production deployment successful"
            ],
            "delivery_approach": "Short time-boxed sprints with continuous delivery",
            "stakeholder_collaboration": "Sprint reviews and continuous feedback",
            "notes": "Works from discovery-ready backlog with reduced rework"
        })
    
    # Wave 4: Discovery Track - Batch 2 (Complex/Critical Systems)
    discovery_batch_2 = needs_discovery[len(needs_discovery)//2:] if len(needs_discovery) > 1 else []
    if discovery_batch_2:
        waves.append({
            "wave_number": 4,
            "name": "Discovery Track - Complex Systems",
            "track": "Discovery",
            "track_description": "Deep investigation of complex and critical systems",
            "applications": [w.get("name", "Unknown") for w in discovery_batch_2],
            "duration_weeks": 8,
            "sprint_count": 4,
            "dependencies_satisfied": ["Batch 1 delivery patterns established"],
            "risk_level": "High",
            "success_criteria": [
                "Complex system dependencies mapped",
                "Modernization opportunities identified",
                "Risk mitigation strategies validated",
                "Detailed migration blueprints created"
            ],
            "discovery_activities": [
                "Dependency mapping and analysis",
                "Modernization feasibility assessment",
                "Risk analysis and mitigation planning",
                "Detailed solution architecture"
            ],
            "delivery_approach": "Extended discovery for complex systems",
            "stakeholder_collaboration": "Intensive stakeholder workshops and validation",
            "notes": "Thorough investigation for high-risk, complex workloads"
        })
    
    # Wave 5: Delivery Track - Complex Systems
    if discovery_batch_2:
        waves.append({
            "wave_number": 5,
            "name": "Delivery Track - Complex Systems",
            "track": "Delivery",
            "track_description": "Careful delivery of complex and critical systems",
            "applications": [w.get("name", "Unknown") for w in discovery_batch_2],
            "duration_weeks": 12,
            "sprint_count": 6,
            "dependencies_satisfied": ["Complex systems discovery completed"],
            "risk_level": "High",
            "success_criteria": [
                "Complex systems migrated with zero downtime",
                "Business continuity maintained",
                "Performance and security validated",
                "Continuous improvement processes established"
            ],
            "delivery_approach": "Careful incremental delivery with extensive testing",
            "stakeholder_collaboration": "Continuous monitoring and feedback",
            "notes": "Validated-then-built approach for complex systems"
        })
    
    total_duration = sum(wave.get("duration_weeks", 0) for wave in waves)
    total_sprints = sum(wave.get("sprint_count", 0) for wave in waves)
    
    return {
        "methodology": "Dual-Track Agile Delivery",
        "methodology_description": "Discovery Track investigates user needs and technical feasibility one sprint ahead, while Delivery Track builds validated migration increments in time-boxed sprints",
        "total_waves": len(waves),
        "total_sprints": total_sprints,
        "estimated_duration_months": round(total_duration / 4.33, 1),  # Convert weeks to months
        "key_principles": [
            "Discovery Track runs one sprint ahead of Delivery Track",
            "Continuous flow of validated-then-built work",
            "Embedded stakeholder collaboration throughout",
            "Reduced rework through validation before building",
            "Rapid incremental delivery of migrated workloads"
        ],
        "waves": waves
    }


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


def optimise_wave_sequence(wave_groups: List[WaveGroup]) -> List[WaveGroup]:
    """
    Optimise the wave sequence based on dependencies and risk levels.
    
    Args:
        wave_groups: List of wave groups to optimise
        
    Returns:
        Optimised list of wave groups
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