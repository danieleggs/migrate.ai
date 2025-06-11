"""
Workload Classifier Agent

This agent handles classification and analysis of applications/workloads
from discovery data for migration planning.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.proposal_generation import ProposalState, Application, WorkloadComplexity
from ..utils.json_parser import parse_llm_json_response


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def classify_workloads(state: ProposalState) -> Dict[str, Any]:
    """
    Classify and analyze workloads from discovery data.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with classified workload data
    """
    try:
        workload_data = state.workload_classification
        
        if not workload_data:
            return {"errors": ["No workload data available for classification"]}
        
        # Extract applications from the workload data
        applications = _extract_applications(workload_data)
        
        # Classify each application
        classified_apps = []
        for app in applications:
            classified_app = _classify_single_workload(app)
            classified_apps.append(classified_app)
        
        return {
            "classified_workloads": classified_apps,
            "workload_summary": _generate_workload_summary(classified_apps)
        }
        
    except Exception as e:
        return {
            "errors": [f"Workload classification failed: {str(e)}"]
        }


def _extract_applications(workload_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract application list from workload data."""
    if isinstance(workload_data, dict):
        # Try different possible keys for applications
        for key in ['applications', 'apps', 'workloads', 'systems']:
            if key in workload_data and isinstance(workload_data[key], list):
                return workload_data[key]
        
        # If no list found, treat the entire dict as a single application
        return [workload_data]
    
    elif isinstance(workload_data, list):
        return workload_data
    
    else:
        # Convert string or other types to a single application entry
        return [{"name": "Unknown Application", "details": str(workload_data)}]


def _classify_single_workload(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """Classify a single workload using LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert cloud migration consultant. Analyze the provided application data and classify it for migration planning.

For each application, determine:
1. Application type (web app, database, API, batch job, etc.)
2. Technology stack (languages, frameworks, databases)
3. Complexity level (Low, Medium, High)
4. Migration readiness (Ready, Needs Assessment, Complex)
5. Business criticality (Low, Medium, High, Critical)
6. Dependencies (internal/external systems)
7. Estimated effort (person-weeks)

Return structured JSON with this classification information.

JSON format:
{
  "name": "Application Name",
  "type": "application_type",
  "technology_stack": ["tech1", "tech2"],
  "complexity": "Low|Medium|High",
  "migration_readiness": "Ready|Needs Assessment|Complex",
  "business_criticality": "Low|Medium|High|Critical",
  "dependencies": ["dep1", "dep2"],
  "estimated_effort_weeks": number,
  "notes": "Additional observations"
}"""),
        ("user", "Classify this application for migration:\n\n{app_data}")
    ])
    
    response = llm.invoke(prompt.format_messages(app_data=str(app_data)))
    
    classified = parse_llm_json_response(
        response.content,
        fallback_data={
            "name": app_data.get("name", "Unknown Application"),
            "type": "Unknown",
            "complexity": "Medium",
            "migration_readiness": "Needs Assessment",
            "business_criticality": "Medium",
            "estimated_effort_weeks": 4
        }
    )
    
    return classified


def _generate_workload_summary(classified_apps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics for classified workloads."""
    if not classified_apps:
        return {}
    
    total_apps = len(classified_apps)
    
    # Count by complexity
    complexity_counts = {}
    readiness_counts = {}
    criticality_counts = {}
    total_effort = 0
    
    for app in classified_apps:
        # Complexity distribution
        complexity = app.get("complexity", "Medium")
        complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        # Readiness distribution
        readiness = app.get("migration_readiness", "Needs Assessment")
        readiness_counts[readiness] = readiness_counts.get(readiness, 0) + 1
        
        # Criticality distribution
        criticality = app.get("business_criticality", "Medium")
        criticality_counts[criticality] = criticality_counts.get(criticality, 0) + 1
        
        # Total effort
        effort = app.get("estimated_effort_weeks", 0)
        if isinstance(effort, (int, float)):
            total_effort += effort
    
    return {
        "total_applications": total_apps,
        "complexity_distribution": complexity_counts,
        "readiness_distribution": readiness_counts,
        "criticality_distribution": criticality_counts,
        "total_estimated_effort_weeks": total_effort,
        "average_effort_per_app": round(total_effort / total_apps, 1) if total_apps > 0 else 0
    }


def validate_applications(applications: List[Application]) -> List[str]:
    """
    Validate the extracted applications for completeness and consistency.
    
    Args:
        applications: List of Application objects to validate
        
    Returns:
        List of validation warnings
    """
    warnings = []
    
    if not applications:
        warnings.append("No applications were extracted from the discovery data")
        return warnings
    
    for app in applications:
        # Check for missing critical information
        if not app.technology_stack:
            warnings.append(f"Application '{app.name}' has no technology stack defined")
        
        if not app.description or len(app.description) < 10:
            warnings.append(f"Application '{app.name}' has insufficient description")
        
        if not app.current_environment:
            warnings.append(f"Application '{app.name}' has no current environment specified")
        
        # Check for potential dependency issues
        if app.dependencies:
            for dep in app.dependencies:
                if not any(dep.lower() in other_app.name.lower() for other_app in applications):
                    warnings.append(
                        f"Application '{app.name}' depends on '{dep}' which was not found in the application list"
                    )
    
    return warnings


def enrich_application_data(applications: List[Application], discovery_data: Dict[str, Any]) -> List[Application]:
    """
    Enrich application data with additional context from discovery data.
    
    Args:
        applications: List of applications to enrich
        discovery_data: Original discovery data for context
        
    Returns:
        List of enriched applications
    """
    # Add business context if available
    business_requirements = discovery_data.get("business_requirements", {})
    infrastructure = discovery_data.get("infrastructure", {})
    
    for app in applications:
        # Enrich with infrastructure context
        if not app.current_environment and infrastructure.get("current_hosting"):
            app.current_environment = infrastructure["current_hosting"]
        
        # Add compliance requirements from business context
        if business_requirements.get("compliance_requirements"):
            existing_compliance = set(app.compliance_requirements)
            business_compliance = set(business_requirements["compliance_requirements"])
            app.compliance_requirements = list(existing_compliance.union(business_compliance))
    
    return applications 