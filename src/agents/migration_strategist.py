"""
Migration Strategist Agent

This agent handles 6R strategy classification and modernization bias
for each application in the migration portfolio.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.proposal_generation import ProposalState, MigrationStrategy, WorkloadComplexity
from ..utils.json_parser import parse_llm_json_response


# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def classify_migration_strategies(state: ProposalState) -> Dict[str, Any]:
    """
    Classify migration strategies for each workload using the 6 R's framework.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with migration strategy classifications
    """
    try:
        classified_workloads = state.classified_workloads
        
        if not classified_workloads:
            return {"errors": ["No classified workloads available for strategy classification"]}
        
        # Classify strategy for each workload
        strategy_classifications = []
        for workload in classified_workloads:
            try:
                strategy = _classify_single_strategy(workload)
                strategy_classifications.append(strategy)
            except Exception as e:
                # If LLM classification fails, use fallback
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    print(f"Rate limit hit, using fallback strategy for {workload.get('name', 'Unknown')}")
                    strategy = _create_fallback_strategy(workload)
                    strategy_classifications.append(strategy)
                else:
                    raise e
        
        # Convert to dictionary format expected by other agents
        migration_strategies = {}
        for strategy in strategy_classifications:
            app_name = strategy.get("application_name", "Unknown")
            migration_strategies[app_name] = strategy.get("recommended_strategy", "replatform")
        
        return {
            "migration_strategies": migration_strategies,
            "strategy_summary": _generate_strategy_summary(strategy_classifications)
        }
        
    except Exception as e:
        return {
            "errors": [f"Strategy classification failed: {str(e)}"]
        }


def _classify_single_strategy(workload: Dict[str, Any]) -> Dict[str, Any]:
    """Classify migration strategy for a single workload using 6R framework."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert cloud migration strategist specializing in the 6R migration framework with modernization bias.

Analyze the provided workload and recommend the optimal migration strategy using the 6R framework:

**6R Migration Strategies:**
1. **Rehost** (Lift & Shift): Move as-is to cloud with minimal changes
    2. **Replatform** (Lift & Reshape): Minor optimisations during migration
3. **Refactor** (Re-architect): Significant code changes to leverage cloud-native features
4. **Repurchase** (Replace): Move to SaaS solution
5. **Retire**: Decommission if no longer needed
6. **Retain** (Revisit): Keep on-premises for now

**Modernization Bias Considerations:**
- Favor cloud-native approaches when feasible
- Consider containerization and microservices opportunities
- Evaluate serverless potential for appropriate workloads
- Assess API-first and event-driven architecture benefits
- Balance modernization benefits with migration complexity and timeline

**Decision Factors:**
- Technical complexity and dependencies
- Business criticality and compliance requirements
- Development team capabilities
- Timeline and budget constraints
- Long-term strategic value

Return JSON format:
{{
  "application_name": "App Name",
  "recommended_strategy": "rehost|replatform|refactor|repurchase|retire|retain",
  "modernization_opportunities": ["opportunity1", "opportunity2"],
  "rationale": "Detailed explanation of strategy choice",
  "effort_estimate_weeks": number,
  "risk_level": "Low|Medium|High",
  "prerequisites": ["prereq1", "prereq2"],
  "success_metrics": ["metric1", "metric2"]
}}"""),
        ("user", "Classify the migration strategy for this workload:\n\n{workload}")
    ])
    
    response = llm.invoke(prompt.format_messages(workload=str(workload)))
    
    strategy = parse_llm_json_response(
        response.content,
        fallback_data={
            "application_name": workload.get("name", "Unknown Application"),
            "recommended_strategy": "replatform",
            "modernization_opportunities": [],
            "rationale": "Default replatform strategy selected",
            "effort_estimate_weeks": 6,
            "risk_level": "Medium",
            "prerequisites": [],
            "success_metrics": ["Successful migration", "Performance maintained"]
        }
    )
    
    return strategy


def _create_fallback_strategy(workload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a fallback migration strategy when LLM is unavailable."""
    
    app_name = workload.get("name", "Unknown Application")
    complexity = workload.get("complexity", "Medium").lower()
    migration_readiness = workload.get("migration_readiness", "Needs Assessment").lower()
    business_criticality = workload.get("business_criticality", "Medium").lower()
    tech_stack = workload.get("technology_stack", [])
    
    # Apply Modernize.AI principles - prefer modernization over lift-and-shift
    if complexity == "low" and "ready" in migration_readiness:
        if any("docker" in tech.lower() or "container" in tech.lower() for tech in tech_stack):
            # Already containerized - good for refactor
            recommended_strategy = "refactor"
            modernization_opportunities = ["Container orchestration", "Cloud-native patterns", "Microservices"]
            effort_weeks = 6
            risk_level = "Medium"
        else:
            # Simple workload - replatform to get cloud benefits
            recommended_strategy = "replatform"
            modernization_opportunities = ["Managed services", "Auto-scaling", "Cloud monitoring"]
            effort_weeks = 4
            risk_level = "Low"
    
    elif complexity == "medium":
        if "critical" in business_criticality:
            # Critical medium complexity - careful replatform
            recommended_strategy = "replatform"
            modernization_opportunities = ["Managed databases", "Load balancing", "Backup automation"]
            effort_weeks = 8
            risk_level = "Medium"
        else:
            # Medium complexity - good candidate for refactor
            recommended_strategy = "refactor"
            modernization_opportunities = ["API modernization", "Database optimization", "Security hardening"]
            effort_weeks = 10
            risk_level = "Medium"
    
    else:  # High complexity
        if "legacy" in app_name.lower() or any("2012" in tech for tech in tech_stack):
            # Legacy system - consider repurchase or major refactor
            if "critical" in business_criticality:
                recommended_strategy = "refactor"
                modernization_opportunities = ["Complete modernization", "Cloud-native rebuild", "API-first design"]
                effort_weeks = 16
                risk_level = "High"
            else:
                recommended_strategy = "repurchase"
                modernization_opportunities = ["SaaS replacement", "Modern alternatives"]
                effort_weeks = 12
                risk_level = "Medium"
        else:
            # Complex but modern - replatform with enhancements
            recommended_strategy = "replatform"
            modernization_opportunities = ["Performance optimization", "Scalability improvements", "Cost optimization"]
            effort_weeks = 12
            risk_level = "High"
    
    return {
        "application_name": app_name,
        "recommended_strategy": recommended_strategy,
        "modernization_opportunities": modernization_opportunities,
        "rationale": f"Fallback strategy based on {complexity} complexity and {business_criticality} criticality",
        "effort_estimate_weeks": effort_weeks,
        "risk_level": risk_level,
        "prerequisites": ["Infrastructure assessment", "Dependency mapping"],
        "success_metrics": ["Migration completed", "Performance maintained", "Cost targets met"]
    }


def _generate_strategy_summary(strategy_classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary of migration strategy classifications."""
    if not strategy_classifications:
        return {}
    
    # Count strategies
    strategy_counts = {}
    total_effort = 0
    risk_distribution = {}
    modernization_opportunities = []
    
    for classification in strategy_classifications:
        # Strategy distribution
        strategy = classification.get("recommended_strategy", "replatform")
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        # Total effort
        effort = classification.get("effort_estimate_weeks", 0)
        if isinstance(effort, (int, float)):
            total_effort += effort
        
        # Risk distribution
        risk = classification.get("risk_level", "Medium")
        risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        
        # Collect modernization opportunities
        opportunities = classification.get("modernization_opportunities", [])
        modernization_opportunities.extend(opportunities)
    
    # Count unique modernization opportunities
    unique_opportunities = {}
    for opp in modernization_opportunities:
        unique_opportunities[opp] = unique_opportunities.get(opp, 0) + 1
    
    return {
        "total_applications": len(strategy_classifications),
        "strategy_distribution": strategy_counts,
        "total_effort_weeks": total_effort,
        "average_effort_per_app": round(total_effort / len(strategy_classifications), 1),
        "risk_distribution": risk_distribution,
        "top_modernization_opportunities": dict(sorted(unique_opportunities.items(), key=lambda x: x[1], reverse=True)[:5])
    }


def apply_modernization_bias(state: ProposalState) -> Dict[str, Any]:
    """
    Apply modernization bias to upgrade strategies where appropriate.
    
    Args:
        state: Current proposal generation state
        
    Returns:
        Dictionary with updated strategies and modernization recommendations
    """
    try:
        updated_strategies = state.migration_strategies.copy()
        feedback_loops = []
        modernization_upgrades = {}
        
        for app_name, strategy in state.migration_strategies.items():
            # Find the application
            app = next((a for a in state.applications if a.name == app_name), None)
            if not app:
                continue
            
            upgrade_reason = None
            new_strategy = strategy
            
            # Apply modernization bias rules
            if strategy == MigrationStrategy.REHOST:
                # Consider upgrading rehost to replatform
                if app.criticality in [WorkloadComplexity.MEDIUM, WorkloadComplexity.HIGH]:
                    if _has_modernization_potential(app):
                        new_strategy = MigrationStrategy.REPLATFORM
                        upgrade_reason = f"Upgraded from rehost to replatform due to {app.criticality.value} criticality and modernization potential"
                
                # Consider upgrading to refactor for high-value applications
                elif app.criticality == WorkloadComplexity.CRITICAL and _is_cloud_native_candidate(app):
                    new_strategy = MigrationStrategy.REFACTOR
                    upgrade_reason = f"Upgraded from rehost to refactor due to critical business importance and cloud-native potential"
            
            elif strategy == MigrationStrategy.REPLATFORM:
                # Consider upgrading replatform to refactor for strategic applications
                if app.criticality == WorkloadComplexity.CRITICAL and _has_high_modernization_value(app):
                    new_strategy = MigrationStrategy.REFACTOR
                    upgrade_reason = f"Upgraded from replatform to refactor due to critical importance and high modernization value"
            
            # Apply the upgrade if determined
            if new_strategy != strategy:
                updated_strategies[app_name] = new_strategy
                modernization_upgrades[app_name] = {
                    "original_strategy": strategy.value,
                    "new_strategy": new_strategy.value,
                    "reason": upgrade_reason
                }
                feedback_loops.append("modernisation_upgrade")
        
        return {
            "migration_strategies": updated_strategies,
            "modernization_upgrades": modernization_upgrades,
            "feedback_loops": feedback_loops
        }
        
    except Exception as e:
        return {
            "errors": [f"Modernization bias application failed: {str(e)}"]
        }


def _has_modernization_potential(app) -> bool:
    """Check if application has modernization potential."""
    modern_technologies = {
        'java', 'python', 'node.js', 'javascript', 'typescript', 'go', 'rust',
        'spring', 'django', 'express', 'react', 'angular', 'vue',
        'docker', 'kubernetes', 'microservices'
    }
    
    app_tech_lower = [tech.lower() for tech in app.technology_stack]
    return any(tech in ' '.join(app_tech_lower) for tech in modern_technologies)


def _is_cloud_native_candidate(app) -> bool:
    """Check if application is a good candidate for cloud-native refactoring."""
    cloud_native_indicators = {
        'api', 'rest', 'microservice', 'docker', 'container',
        'spring boot', 'node.js', 'serverless', 'lambda'
    }
    
    app_tech_lower = [tech.lower() for tech in app.technology_stack]
    description_lower = app.description.lower()
    
    return (
        any(indicator in ' '.join(app_tech_lower) for indicator in cloud_native_indicators) or
        any(indicator in description_lower for indicator in cloud_native_indicators) or
        app.estimated_users and app.estimated_users > 10000  # High-scale applications
    )


def _has_high_modernization_value(app) -> bool:
    """Check if application has high value for modernization investment."""
    return (
        app.criticality == WorkloadComplexity.CRITICAL and
        (app.estimated_users and app.estimated_users > 5000) and
        _has_modernization_potential(app)
    )


def validate_strategy_assignments(applications: List, strategies: Dict[str, MigrationStrategy]) -> List[str]:
    """
    Validate strategy assignments for consistency and completeness.
    
    Args:
        applications: List of applications
        strategies: Dictionary of strategy assignments
        
    Returns:
        List of validation warnings
    """
    warnings = []
    
    app_names = {app.name for app in applications}
    strategy_apps = set(strategies.keys())
    
    # Check for missing strategies
    missing_strategies = app_names - strategy_apps
    if missing_strategies:
        warnings.append(f"No migration strategy assigned to: {', '.join(missing_strategies)}")
    
    # Check for extra strategies
    extra_strategies = strategy_apps - app_names
    if extra_strategies:
        warnings.append(f"Migration strategies assigned to unknown applications: {', '.join(extra_strategies)}")
    
    # Check for strategy distribution
    strategy_counts = {}
    for strategy in strategies.values():
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    total_apps = len(applications)
    if total_apps > 0:
        rehost_percentage = strategy_counts.get(MigrationStrategy.REHOST, 0) / total_apps
        if rehost_percentage > 0.7:
            warnings.append(f"High percentage of rehost strategies ({rehost_percentage:.1%}) - consider more modernization")
        
        retire_percentage = strategy_counts.get(MigrationStrategy.RETIRE, 0) / total_apps
        if retire_percentage > 0.3:
            warnings.append(f"High percentage of retire strategies ({retire_percentage:.1%}) - verify these are truly obsolete")
    
    return warnings


def generate_strategy_summary(strategies: Dict[str, MigrationStrategy]) -> Dict[str, Any]:
    """
    Generate a summary of the migration strategy distribution.
    
    Args:
        strategies: Dictionary of strategy assignments
        
    Returns:
        Dictionary with strategy summary metrics
    """
    if not strategies:
        return {}
    
    strategy_counts = {}
    for strategy in strategies.values():
        strategy_counts[strategy.value] = strategy_counts.get(strategy.value, 0) + 1
    
    total_apps = len(strategies)
    strategy_percentages = {
        strategy: (count / total_apps) * 100
        for strategy, count in strategy_counts.items()
    }
    
    modernization_score = (
        strategy_counts.get("refactor", 0) * 3 +
        strategy_counts.get("replatform", 0) * 2 +
        strategy_counts.get("repurchase", 0) * 2
    ) / (total_apps * 3) if total_apps > 0 else 0
    
    return {
        "total_applications": total_apps,
        "strategy_counts": strategy_counts,
        "strategy_percentages": strategy_percentages,
        "modernization_score": modernization_score,
        "recommended_approach": _get_recommended_approach(strategy_percentages)
    }


def _get_recommended_approach(percentages: Dict[str, float]) -> str:
    """Get recommended migration approach based on strategy distribution."""
    rehost_pct = percentages.get("rehost", 0)
    replatform_pct = percentages.get("replatform", 0)
    refactor_pct = percentages.get("refactor", 0)
    
    if refactor_pct > 40:
        return "Transformation-focused: High modernization with significant cloud-native adoption"
    elif replatform_pct + refactor_pct > 60:
        return "Modernisation-focused: Balanced approach with substantial cloud optimisation"
    elif rehost_pct > 60:
        return "Migration-focused: Rapid cloud adoption with future modernization phases"
    else:
        return "Hybrid approach: Mixed strategy based on application-specific needs" 