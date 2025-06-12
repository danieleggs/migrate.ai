"""
Remaining Proposal Generation Agents

This module contains the remaining agents for proposal generation:
- Architecture Advisor
- GenAI Tool Planner  
- Sprint Effort Estimator
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.proposal_generation import ProposalState
from ..utils.json_parser import parse_llm_json_response


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def provide_architecture_advice(state: ProposalState) -> Dict[str, Any]:
    """
    Provide architecture recommendations based on migration strategies.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with architecture recommendations
    """
    try:
        migration_strategies = state.migration_strategies
        
        if not migration_strategies:
            return {"errors": ["No migration strategies available for architecture advice"]}
        
        # Generate architecture recommendations
        recommendations = _generate_architecture_recommendations(migration_strategies)
        
        return {
            "architecture_recommendations": recommendations
        }
        
    except Exception as e:
        return {
            "errors": [f"Architecture advice generation failed: {str(e)}"]
        }


def plan_genai_tools(state: ProposalState) -> Dict[str, Any]:
    """
    Plan GenAI tools and automation opportunities.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with GenAI tool recommendations
    """
    try:
        classified_workloads = state.classified_workloads
        migration_strategies = state.migration_strategies
        
        if not classified_workloads:
            return {"errors": ["No workload data available for GenAI planning"]}
        
        # Generate GenAI tool recommendations
        genai_plan = _generate_genai_recommendations(classified_workloads, migration_strategies)
        
        return {
            "genai_recommendations": genai_plan
        }
        
    except Exception as e:
        return {
            "errors": [f"GenAI planning failed: {str(e)}"]
        }


def estimate_sprint_efforts(state: ProposalState) -> Dict[str, Any]:
    """
    Estimate sprint efforts for migration waves.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with sprint effort estimates
    """
    try:
        migration_waves = state.migration_waves
        migration_strategies = state.migration_strategies
        
        if not migration_waves:
            return {"errors": ["No migration waves available for effort estimation"]}
        
        # Generate sprint effort estimates
        effort_estimates = _generate_effort_estimates(migration_waves, migration_strategies)
        
        return {
            "effort_estimates": effort_estimates
        }
        
    except Exception as e:
        return {
            "errors": [f"Sprint effort estimation failed: {str(e)}"]
        }


def _generate_architecture_recommendations(migration_strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate architecture recommendations using LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a cloud architecture expert providing recommendations for migration projects.

Based on the migration strategies for each application, provide comprehensive architecture recommendations including:

**Cloud Architecture Patterns:**
- Microservices vs Monolithic considerations
- API Gateway and service mesh recommendations
- Data architecture and storage patterns
- Security architecture and compliance
- Monitoring and observability strategy

**Technology Recommendations:**
- Container orchestration (Kubernetes, ECS, etc.)
- Serverless opportunities (Lambda, Functions)
- Database modernization (managed services, NoSQL)
- Integration patterns (event-driven, messaging)
- DevOps and CI/CD pipeline architecture

**Best Practices:**
- Cloud-native design principles
- Scalability and performance optimisation
- Cost optimisation strategies
- Disaster recovery and backup
- Security and compliance frameworks

Return JSON format:
{{
  "architecture_patterns": ["pattern1", "pattern2"],
  "technology_stack": {{
    "compute": ["service1", "service2"],
    "storage": ["service1", "service2"],
    "networking": ["service1", "service2"]
  }},
  "recommendations": [
    {{
      "category": "category_name",
      "recommendation": "detailed recommendation",
      "rationale": "why this is recommended",
      "priority": "High|Medium|Low"
    }}
  ]
}}"""),
        ("user", "Provide architecture recommendations based on these migration strategies:\n\n{strategies}")
    ])
    
    strategies_str = str(migration_strategies)
    response = llm.invoke(prompt.format_messages(strategies=strategies_str))
    
    recommendations = parse_llm_json_response(
        response.content,
        fallback_data={
            "architecture_patterns": ["Cloud-native", "Microservices"],
            "technology_stack": {
                "compute": ["Container Services", "Serverless Functions"],
                "storage": ["Managed Databases", "Object Storage"],
                "networking": ["Load Balancers", "API Gateway"]
            },
            "recommendations": [{
                "category": "General",
                "recommendation": "Adopt cloud-native architecture patterns",
                "rationale": "Improved scalability and maintainability",
                "priority": "High"
            }]
        }
    )
    
    return recommendations


def _generate_genai_recommendations(classified_workloads: List[Dict[str, Any]], migration_strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate GenAI tool recommendations using LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI/ML expert specializing in GenAI tools for cloud migration and modernization.

Analyze the workloads and migration strategies to recommend GenAI tools and automation opportunities:

**GenAI Tool Categories:**
1. **Code Modernization**: Tools for code refactoring and modernization
2. **Documentation Generation**: Automated documentation and knowledge transfer
3. **Testing Automation**: AI-powered test generation and validation
4. **Infrastructure as Code**: Automated IaC generation and optimisation
5. **Monitoring and Observability**: AI-driven monitoring and alerting
6. **Security and Compliance**: Automated security scanning and compliance

**Specific Tool Recommendations:**
- GitHub Copilot for code assistance
- AWS CodeWhisperer for cloud-native development
- Automated testing frameworks
- Infrastructure automation tools
- Documentation generation tools

**Implementation Strategy:**
- Pilot programs and proof of concepts
- Training and adoption roadmap
- ROI measurement and success metrics

Return JSON format:
{{
  "tool_categories": [
    {{
      "category": "category_name",
      "tools": ["tool1", "tool2"],
      "use_cases": ["use_case1", "use_case2"],
      "expected_benefits": ["benefit1", "benefit2"],
      "implementation_effort": "Low|Medium|High"
    }}
  ],
  "automation_opportunities": [
    {{
      "opportunity": "automation description",
      "potential_savings": "time/cost savings",
      "complexity": "Low|Medium|High"
    }}
  ]
}}"""),
        ("user", "Recommend GenAI tools for these workloads and migration strategies:\n\nWorkloads: {workloads}\n\nStrategies: {strategies}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        workloads=str(classified_workloads),
        strategies=str(migration_strategies)
    ))
    
    genai_plan = parse_llm_json_response(
        response.content,
        fallback_data={
            "tool_categories": [{
                "category": "Code Modernization",
                "tools": ["GitHub Copilot", "AWS CodeWhisperer"],
                "use_cases": ["Code refactoring", "Cloud-native development"],
                "expected_benefits": ["Faster development", "Improved code quality"],
                "implementation_effort": "Medium"
            }],
            "automation_opportunities": [{
                "opportunity": "Automated code review and refactoring",
                "potential_savings": "30% reduction in development time",
                "complexity": "Medium"
            }]
        }
    )
    
    return genai_plan


def _generate_effort_estimates(migration_waves: Dict[str, Any], migration_strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate sprint effort estimates using LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a project management expert specializing in agile migration projects.

Analyze the migration waves and strategies to provide detailed sprint effort estimates:

**Estimation Factors:**
- Application complexity and size
- Migration strategy (rehost vs refactor complexity)
- Dependencies and integration requirements
- Team experience and capabilities
- Testing and validation requirements
- Risk mitigation activities

**Sprint Planning:**
- Standard 2-week sprint cycles
- Team capacity and velocity considerations
- Buffer time for unknowns and risks
- Parallel work streams where possible

**Deliverables per Sprint:**
- Development and migration activities
- Testing and validation milestones
- Documentation and knowledge transfer
- Go-live and cutover activities

Return JSON format:
{{
  "total_project_duration_weeks": number,
  "total_sprint_count": number,
  "wave_estimates": [
    {{
      "wave_number": number,
      "wave_name": "name",
      "duration_weeks": number,
      "sprint_count": number,
      "team_size": number,
      "effort_person_weeks": number,
      "key_milestones": ["milestone1", "milestone2"],
      "risk_factors": ["risk1", "risk2"]
    }}
  ],
  "resource_requirements": {{
    "developers": number,
    "architects": number,
    "devops_engineers": number,
    "testers": number
  }}
}}"""),
        ("user", "Estimate sprint efforts for these migration waves and strategies:\n\nWaves: {waves}\n\nStrategies: {strategies}")
    ])
    
    response = llm.invoke(prompt.format_messages(
        waves=str(migration_waves),
        strategies=str(migration_strategies)
    ))
    
    effort_estimates = parse_llm_json_response(
        response.content,
        fallback_data={
            "total_project_duration_weeks": 24,
            "total_sprint_count": 12,
            "wave_estimates": [{
                "wave_number": 1,
                "wave_name": "Initial Wave",
                "duration_weeks": 8,
                "sprint_count": 4,
                "team_size": 5,
                "effort_person_weeks": 40,
                "key_milestones": ["Migration complete", "Testing complete"],
                "risk_factors": ["Technical complexity", "Resource availability"]
            }],
            "resource_requirements": {
                "developers": 3,
                "architects": 1,
                "devops_engineers": 1,
                "testers": 1
            }
        }
    )
    
    return effort_estimates 