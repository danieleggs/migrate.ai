"""
Workload Classifier Agent

This agent handles classification and analysis of applications/workloads
from discovery data for migration planning.
"""

import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.proposal_generation import ProposalState, Application, WorkloadComplexity
from ..utils.json_parser import parse_llm_json_response

# Testing mode - set FORCE_FALLBACK=true to test without API calls
FORCE_FALLBACK = os.getenv("FORCE_FALLBACK", "false").lower() == "true"

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def classify_workloads(state: ProposalState) -> Dict[str, Any]:
    """
    Classify workloads from discovery data.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with classified workloads and summary
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
            try:
                classified_app = _classify_single_workload(app)
                classified_apps.append(classified_app)
            except Exception as e:
                # If LLM classification fails (e.g., rate limiting), use fallback
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    print(f"Rate limit hit, using fallback classification for {app.get('name', 'Unknown')}")
                    classified_app = _create_fallback_classification(app)
                    classified_apps.append(classified_app)
                else:
                    # Re-raise other errors
                    raise e
        
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
    applications = []
    
    if isinstance(workload_data, dict):
        # Try different possible keys for applications
        for key in ['applications', 'apps', 'workloads', 'systems']:
            if key in workload_data and isinstance(workload_data[key], list):
                applications.extend(workload_data[key])
        
        # Check for infrastructure data (servers, databases, etc.)
        if 'infrastructure' in workload_data:
            infrastructure = workload_data['infrastructure']
            
            # Convert servers to workloads
            if 'servers' in infrastructure and isinstance(infrastructure['servers'], list):
                for server in infrastructure['servers']:
                    server_workload = {
                        "name": server.get('server_name', 'Unknown Server'),
                        "type": "server",
                        "os": server.get('os', 'Unknown OS'),
                        "cpu_cores": server.get('cpu_cores', 0),
                        "memory_gb": server.get('memory_gb', 0),
                        "storage_gb": server.get('storage_gb', 0),
                        "current_environment": "on-premises",
                        "description": f"Server running {server.get('os', 'Unknown OS')}"
                    }
                    applications.append(server_workload)
            
            # Convert databases to workloads
            if 'databases' in infrastructure and isinstance(infrastructure['databases'], list):
                for db in infrastructure['databases']:
                    db_workload = {
                        "name": db.get('database_name', 'Unknown Database'),
                        "type": "database",
                        "database_type": db.get('database_type', 'Unknown'),
                        "version": db.get('version', 'Unknown'),
                        "current_environment": "on-premises",
                        "description": f"Database: {db.get('database_type', 'Unknown')}"
                    }
                    applications.append(db_workload)
        
        # If no applications found, treat the entire dict as a single application
        if not applications:
            applications = [workload_data]
    
    elif isinstance(workload_data, list):
        applications = workload_data
    
    else:
        # Convert string or other types to a single application entry
        applications = [{"name": "Unknown Application", "details": str(workload_data)}]
    
    return applications


def _classify_single_workload(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """Classify a single workload using LLM."""
    
    # Force fallback for testing if environment variable is set
    if FORCE_FALLBACK:
        print(f"FORCE_FALLBACK enabled - using fallback classification for {app_data.get('name', 'Unknown')}")
        return _create_fallback_classification(app_data)
    
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
{{
  "name": "Application Name",
  "type": "application_type",
  "technology_stack": ["tech1", "tech2"],
  "complexity": "Low|Medium|High",
  "migration_readiness": "Ready|Needs Assessment|Complex",
  "business_criticality": "Low|Medium|High|Critical",
  "dependencies": ["dep1", "dep2"],
  "estimated_effort_weeks": number,
  "notes": "Additional observations"
}}"""),
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


def _create_fallback_classification(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a fallback classification when LLM is unavailable."""
    
    app_name = app_data.get("name", "Unknown Application")
    app_type = app_data.get("type", "server")
    os_info = app_data.get("os", "").lower()
    
    # Smart fallback based on available data
    if "windows" in os_info and "server" in os_info:
        if "2012" in os_info:
            complexity = "High"  # Legacy OS
            migration_readiness = "Complex"
            effort_weeks = 8
        elif "2016" in os_info:
            complexity = "Medium"
            migration_readiness = "Needs Assessment"
            effort_weeks = 6
        else:  # 2019+
            complexity = "Medium"
            migration_readiness = "Ready"
            effort_weeks = 4
    elif "linux" in os_info or "ubuntu" in os_info or "centos" in os_info:
        complexity = "Low"
        migration_readiness = "Ready"
        effort_weeks = 3
    else:
        complexity = "Medium"
        migration_readiness = "Needs Assessment"
        effort_weeks = 4
    
    # Determine criticality based on server specs or type
    cpu_cores = app_data.get("cpu_cores", 0)
    memory_gb = app_data.get("memory_gb", 0)
    
    if cpu_cores >= 16 or memory_gb >= 64:
        business_criticality = "Critical"
    elif cpu_cores >= 8 or memory_gb >= 32:
        business_criticality = "High"
    elif cpu_cores >= 4 or memory_gb >= 16:
        business_criticality = "Medium"
    else:
        business_criticality = "Low"
    
    # Determine technology stack
    tech_stack = []
    if "windows" in os_info:
        tech_stack.extend(["Windows Server", "IIS"])
        if "sql" in app_name.lower():
            tech_stack.append("SQL Server")
        if "web" in app_name.lower():
            tech_stack.extend([".NET", "ASP.NET"])
    elif "linux" in os_info:
        tech_stack.extend(["Linux", "Apache"])
        if "docker" in app_name.lower():
            tech_stack.extend(["Docker", "Containers"])
        if "app" in app_name.lower():
            tech_stack.extend(["Node.js", "Python"])
    
    return {
        "name": app_name,
        "type": app_type,
        "technology_stack": tech_stack or ["Unknown"],
        "complexity": complexity,
        "migration_readiness": migration_readiness,
        "business_criticality": business_criticality,
        "dependencies": [],
        "estimated_effort_weeks": effort_weeks,
        "notes": f"Fallback classification for {app_type} - requires detailed assessment"
    }


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