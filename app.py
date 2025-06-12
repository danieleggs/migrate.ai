import streamlit as st
import os
from dotenv import load_dotenv
import yaml
from typing import Dict, Any
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

from src.graph.evaluation_graph import EvaluationOrchestrator
from src.models.evaluation import MigrationPhase
from src.models.evaluation_types import EvaluationType, EVALUATION_CONFIGS
from src.agents.sow_evaluator import evaluate_sow_document
from src.graph.proposal_generation_graph import ProposalGenerationOrchestrator

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="migrate.ai Pre-Sales Evaluator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-card {
        background-color: var(--background-color);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border: 1px solid var(--border-color);
        color: var(--text-color);
    }
    .critical-gap {
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #f44336;
        border-radius: 4px;
    }
    .high-gap {
        background-color: rgba(255, 152, 0, 0.1);
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #ff9800;
        border-radius: 4px;
    }
    .recommendation {
        background-color: rgba(76, 175, 80, 0.1);
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #4caf50;
        border-radius: 4px;
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-color: #ffffff;
            --background-color: #262730;
            --border-color: #464853;
        }
    }
    
    /* Light mode support */
    @media (prefers-color-scheme: light) {
        :root {
            --text-color: #262730;
            --background-color: #ffffff;
            --border-color: #e0e0e0;
        }
    }
    
    /* Force text visibility in dark mode */
    [data-theme="dark"] .stMarkdown,
    [data-theme="dark"] .stText,
    [data-theme="dark"] div[data-testid="stMarkdownContainer"] p,
    [data-theme="dark"] div[data-testid="stMarkdownContainer"] li,
    [data-theme="dark"] div[data-testid="stMarkdownContainer"] strong {
        color: #ffffff !important;
    }
    
    /* Force text visibility in light mode */
    [data-theme="light"] .stMarkdown,
    [data-theme="light"] .stText,
    [data-theme="light"] div[data-testid="stMarkdownContainer"] p,
    [data-theme="light"] div[data-testid="stMarkdownContainer"] li,
    [data-theme="light"] div[data-testid="stMarkdownContainer"] strong {
        color: #262730 !important;
    }
    
    /* Universal text fixes for both themes */
    .stMarkdown p, .stMarkdown li, .stMarkdown strong {
        color: inherit !important;
    }
    
    /* Ensure expander content is visible in both themes */
    .streamlit-expanderContent {
        color: inherit;
    }
    
    /* Fix metric text colors for both themes */
    .metric-container {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--border-color);
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Alert message fixes */
    .stAlert {
        color: inherit !important;
    }
    
    .stAlert > div {
        color: inherit !important;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application function."""
    
    # Initialize session state for caching evaluation results
    if 'evaluation_result' not in st.session_state:
        st.session_state.evaluation_result = None
    if 'evaluation_metadata' not in st.session_state:
        st.session_state.evaluation_metadata = None
    if 'last_file_hash' not in st.session_state:
        st.session_state.last_file_hash = None
    if 'last_eval_type' not in st.session_state:
        st.session_state.last_eval_type = None
    
    # Header
    st.markdown('<h1 class="main-header">Pre-Sales Document Evaluator</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ## Migration-Focused Document Evaluation Tool
    
    Choose from different evaluation types to assess your documents:
    - **Migration Proposals**: Full evaluation against migrate.ai specification
    - **Statement of Work**: Framework for SOW evaluation (logic to be implemented)
    - **Migration Proposal Generator**: Generate comprehensive migration proposals from discovery data
    """)
    
    # Sidebar
    with st.sidebar:
        st.header("Evaluation Configuration")
        
        # Tool selector
        st.subheader("Select Evaluation Type")
        
        # Create options for the selectbox
        evaluation_options = {}
        for eval_type, config in EVALUATION_CONFIGS.items():
            evaluation_options[config.name] = eval_type
        
        selected_option = st.selectbox(
            "Choose evaluation type:",
            options=list(evaluation_options.keys()),
            help="Select the type of document evaluation you want to perform"
        )
        
        selected_eval_type = evaluation_options[selected_option]
        selected_config = EVALUATION_CONFIGS[selected_eval_type]
        
        # Display selected evaluation info
        st.info(f"**{selected_config.name}**\n\n{selected_config.description}")
        
        with st.expander("Evaluation Criteria"):
            for criterion in selected_config.evaluation_criteria:
                st.write(f"• {criterion}")
        
        st.markdown("---")
        
        # API Key check
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
            st.stop()
        else:
            st.success("OpenAI API key configured")
        
        st.markdown("---")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Document",
            type=['pdf', 'docx', 'txt', 'md', 'xlsx', 'xls'],
            help="Upload your document for evaluation (PDF, DOCX, TXT, MD) or Excel file for proposal generation (XLSX, XLS)"
        )
        
        if uploaded_file:
            st.success(f"File uploaded: {uploaded_file.name}")
            st.info(f"File size: {len(uploaded_file.getvalue())} bytes")
        
        # Additional context inputs for Proposal Generator
        proposal_context = {}
        if selected_eval_type == EvaluationType.PROPOSAL_GENERATOR:
            st.markdown("---")
            st.subheader("📋 Project Context")
            
            # Client and project details
            col1, col2 = st.columns(2)
            with col1:
                client_name = st.text_input(
                    "Client Name",
                    value="",
                    placeholder="e.g., Acme Corporation",
                    help="Name of the client organization"
                )
            with col2:
                project_name = st.text_input(
                    "Project Name",
                    value="",
                    placeholder="e.g., Cloud Migration Initiative",
                    help="Name of the migration project"
                )
            
            # Business drivers
            st.markdown("**Business Drivers & Objectives**")
            business_drivers = st.multiselect(
                "Primary drivers for migration:",
                options=[
                    "Cost Optimization",
                    "Digital Transformation",
                    "Scalability & Performance",
                    "Security & Compliance",
                    "Innovation & Agility",
                    "Data Center Exit",
                    "Disaster Recovery",
                    "Modernization",
                    "Competitive Advantage",
                    "Regulatory Requirements"
                ],
                help="Select the main business drivers for this migration"
            )
            
            additional_context = st.text_area(
                "Additional Business Context",
                placeholder="e.g., Legacy system end-of-life, merger integration, new market expansion...",
                help="Any additional context about business drivers, constraints, or objectives"
            )
            
            # Target cloud and preferences
            st.markdown("**Target Environment**")
            col1, col2 = st.columns(2)
            with col1:
                target_cloud = st.selectbox(
                    "Primary Target Cloud",
                    options=["AWS", "Microsoft Azure", "Google Cloud", "Multi-Cloud", "Hybrid", "Not Specified"],
                    index=5,
                    help="Primary cloud platform for migration"
                )
            with col2:
                migration_approach = st.selectbox(
                    "Preferred Migration Approach",
                    options=["Lift & Shift First", "Modernize Where Possible", "Cloud-Native Transformation", "Hybrid Approach", "Not Specified"],
                    index=4,
                    help="Overall approach preference for migration"
                )
            
            # Timeline and constraints
            st.markdown("**Timeline & Constraints**")
            col1, col2 = st.columns(2)
            with col1:
                timeline_constraint = st.selectbox(
                    "Timeline Urgency",
                    options=["Flexible", "Moderate (6-12 months)", "Urgent (3-6 months)", "Critical (<3 months)", "Not Specified"],
                    index=4,
                    help="Overall timeline expectations"
                )
            with col2:
                budget_constraint = st.selectbox(
                    "Budget Considerations",
                    options=["Flexible", "Moderate Budget", "Cost-Conscious", "Minimal Budget", "Not Specified"],
                    index=4,
                    help="Budget constraints for the project"
                )
            
            # Risk tolerance and compliance
            st.markdown("**Risk & Compliance**")
            col1, col2 = st.columns(2)
            with col1:
                risk_tolerance = st.selectbox(
                    "Risk Tolerance",
                    options=["Conservative", "Moderate", "Aggressive", "Not Specified"],
                    index=3,
                    help="Organization's tolerance for migration risks"
                )
            with col2:
                compliance_requirements = st.multiselect(
                    "Compliance Requirements",
                    options=["GDPR", "HIPAA", "SOX", "PCI-DSS", "ISO 27001", "FedRAMP", "SOC 2", "None", "Other"],
                    help="Relevant compliance frameworks"
                )
            
            # Store context for use in proposal generation
            proposal_context = {
                "client_name": client_name or "Client Organization",
                "project_name": project_name or f"Migration Project - {uploaded_file.name if uploaded_file else 'Discovery'}",
                "business_drivers": business_drivers,
                "additional_context": additional_context,
                "target_cloud": target_cloud,
                "migration_approach": migration_approach,
                "timeline_constraint": timeline_constraint,
                "budget_constraint": budget_constraint,
                "risk_tolerance": risk_tolerance,
                "compliance_requirements": compliance_requirements
            }
        
        st.markdown("---")
        
        # Evaluation options (only show if file is uploaded)
        if uploaded_file:
            st.subheader("Display Options")
            show_detailed_analysis = st.checkbox("Show detailed analysis", value=True)
            show_phase_breakdown = st.checkbox("Show phase breakdown", value=True)
            show_recommendations = st.checkbox("Show recommendations", value=True)
            
            st.markdown("---")
            
            # Add re-run button
            if st.button("Re-run Evaluation", help="Force re-evaluation of the document"):
                # Clear cache to force re-evaluation
                st.session_state.evaluation_result = None
                st.session_state.last_file_hash = None
                st.session_state.last_eval_type = None
                st.rerun()
        else:
            show_detailed_analysis = True
            show_phase_breakdown = True
            show_recommendations = True
    
    # Main content area - only show evaluation if file is uploaded
    if uploaded_file is not None:
        run_evaluation_with_cache(uploaded_file, selected_eval_type, selected_config, show_detailed_analysis, show_phase_breakdown, show_recommendations, proposal_context)
    else:
        # Clear cached results when no file is uploaded
        if st.session_state.evaluation_result is not None:
            st.session_state.evaluation_result = None
            st.session_state.evaluation_metadata = None
            st.session_state.last_file_hash = None
            st.session_state.last_eval_type = None
        
        # Blank right pane with just a simple message
        st.markdown("### Upload a document to begin evaluation")
        st.markdown("Select an evaluation type from the sidebar and upload your document to get started.")


def run_evaluation_with_cache(uploaded_file, eval_type, config, show_detailed_analysis, show_phase_breakdown, show_recommendations, proposal_context=None):
    """Run evaluation with caching to avoid re-running on display option changes."""
    
    # Create a hash of the file content to detect changes
    import hashlib
    file_content = uploaded_file.getvalue()
    file_hash = hashlib.md5(file_content).hexdigest()
    
    # Check if we need to re-run the evaluation
    need_evaluation = (
        st.session_state.evaluation_result is None or
        st.session_state.last_file_hash != file_hash or
        st.session_state.last_eval_type != eval_type
    )
    
    if need_evaluation:
        # Show that we're running a new evaluation
        st.subheader(f"{config.name}: {uploaded_file.name}")
        
        # Run the actual evaluation
        result = run_evaluation_core(uploaded_file, eval_type, config, proposal_context)
        
        # Cache the results
        if result and result.get("success"):
            st.session_state.evaluation_result = result
            st.session_state.last_file_hash = file_hash
            st.session_state.last_eval_type = eval_type
        else:
            # Don't cache failed results
            st.session_state.evaluation_result = None
            if result:
                st.error(f"Evaluation failed: {result.get('error', 'Unknown error')}")
                if result.get("partial_results"):
                    st.subheader("Partial Results")
                    st.json(result["partial_results"])
            return
    else:
        # Using cached results - show a subtle indicator
        st.subheader(f"{config.name}: {uploaded_file.name}")
        st.caption("Using cached evaluation results (change file or evaluation type to re-run)")
    
    # Display results (either fresh or cached)
    if st.session_state.evaluation_result:
        result = st.session_state.evaluation_result
        
        if eval_type == EvaluationType.MIGRATION_PROPOSAL:
            display_evaluation_results(result, show_detailed_analysis, show_phase_breakdown, show_recommendations)
        elif eval_type == EvaluationType.STATEMENT_OF_WORK:
            display_sow_results(result, show_detailed_analysis, show_phase_breakdown, show_recommendations)
        elif eval_type == EvaluationType.PROPOSAL_GENERATOR:
            display_proposal_generator_results(result, show_detailed_analysis, show_phase_breakdown, show_recommendations)


def run_evaluation_core(uploaded_file, eval_type, config, proposal_context=None):
    """Core evaluation logic without caching."""
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Get file content
        file_content = uploaded_file.getvalue()
        
        if not file_content:
            st.error("No file content detected!")
            return None
        
        # Route to appropriate evaluator based on type
        if eval_type == EvaluationType.MIGRATION_PROPOSAL:
            # Use existing migration proposal evaluator
            status_text.text("Initializing migration proposal evaluation...")
            progress_bar.progress(10)
            
            orchestrator = EvaluationOrchestrator()
            
            status_text.text("Analyzing migration proposal...")
            progress_bar.progress(30)
            
            result = orchestrator.evaluate_document(file_content, uploaded_file.name)
            
            progress_bar.progress(100)
            status_text.text("Migration evaluation complete!")
            
            return result
        
        elif eval_type == EvaluationType.STATEMENT_OF_WORK:
            # Use placeholder SOW evaluator
            status_text.text("Initializing SOW evaluation framework...")
            progress_bar.progress(10)
            
            status_text.text("Running placeholder SOW analysis...")
            progress_bar.progress(50)
            
            # Parse document content (basic parsing for now)
            try:
                from src.utils.document_parser import DocumentParser
                parsed_doc = DocumentParser.parse_document(file_content, uploaded_file.name)
                content = parsed_doc.content
            except Exception:
                # Fallback to basic content extraction
                content = str(file_content[:1000])  # Simple fallback
            
            result = evaluate_sow_document(content)
            
            progress_bar.progress(100)
            status_text.text("SOW framework evaluation complete!")
            
            # Wrap SOW result in success format
            return {"success": True, "evaluation_result": result}
        
        elif eval_type == EvaluationType.PROPOSAL_GENERATOR:
            # Use proposal generator
            status_text.text("Initializing proposal generation...")
            progress_bar.progress(10)
            
            # Parse document content as discovery data
            try:
                from src.utils.document_parser import DocumentParser
                parsed_doc = DocumentParser.parse_document(file_content, uploaded_file.name)
                content = parsed_doc.content
            except Exception:
                # Fallback to basic content extraction
                content = str(file_content, 'utf-8', errors='ignore')
            
            status_text.text("Analyzing discovery data...")
            progress_bar.progress(30)
            
            # Create discovery input data with context
            if proposal_context:
                discovery_data = {
                    "client_name": proposal_context.get("client_name", "Client Organization"),
                    "project_name": proposal_context.get("project_name", f"Migration Project - {uploaded_file.name}"),
                    "source_type": "text",
                    "raw_data": content,
                    "business_context": _build_business_context(proposal_context),
                    "target_cloud": proposal_context.get("target_cloud", "Not Specified"),
                    "migration_approach": proposal_context.get("migration_approach", "Not Specified"),
                    "timeline_constraint": proposal_context.get("timeline_constraint", "Not Specified"),
                    "budget_constraint": proposal_context.get("budget_constraint", "Not Specified"),
                    "risk_tolerance": proposal_context.get("risk_tolerance", "Not Specified"),
                    "compliance_requirements": proposal_context.get("compliance_requirements", [])
                }
            else:
                # Fallback to default values
                discovery_data = {
                    "client_name": "Client Organization",
                    "project_name": f"Migration Project - {uploaded_file.name}",
                    "source_type": "text",
                    "raw_data": content,
                    "business_context": "Cloud migration and modernization initiative"
                }
            
            status_text.text("Generating migration proposal...")
            progress_bar.progress(50)
            
            # Initialize proposal generator
            proposal_orchestrator = ProposalGenerationOrchestrator()
            
            status_text.text("Running proposal generation workflow...")
            progress_bar.progress(70)
            
            # Generate proposal
            result = proposal_orchestrator.generate_proposal(discovery_data)
            
            progress_bar.progress(100)
            status_text.text("Proposal generation complete!")
            
            return result
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return {"success": False, "error": str(e)}
    finally:
        progress_bar.empty()
        status_text.empty()


def _build_business_context(proposal_context):
    """Build a comprehensive business context string from the proposal context."""
    context_parts = []
    
    # Business drivers
    drivers = proposal_context.get("business_drivers", [])
    if drivers:
        context_parts.append(f"Primary business drivers: {', '.join(drivers)}")
    
    # Additional context
    additional = proposal_context.get("additional_context", "").strip()
    if additional:
        context_parts.append(f"Additional context: {additional}")
    
    # Target environment
    target_cloud = proposal_context.get("target_cloud", "Not Specified")
    if target_cloud != "Not Specified":
        context_parts.append(f"Target cloud platform: {target_cloud}")
    
    migration_approach = proposal_context.get("migration_approach", "Not Specified")
    if migration_approach != "Not Specified":
        context_parts.append(f"Preferred migration approach: {migration_approach}")
    
    # Timeline and budget
    timeline = proposal_context.get("timeline_constraint", "Not Specified")
    if timeline != "Not Specified":
        context_parts.append(f"Timeline expectations: {timeline}")
    
    budget = proposal_context.get("budget_constraint", "Not Specified")
    if budget != "Not Specified":
        context_parts.append(f"Budget considerations: {budget}")
    
    # Risk and compliance
    risk_tolerance = proposal_context.get("risk_tolerance", "Not Specified")
    if risk_tolerance != "Not Specified":
        context_parts.append(f"Risk tolerance: {risk_tolerance}")
    
    compliance = proposal_context.get("compliance_requirements", [])
    if compliance and compliance != ["None"]:
        context_parts.append(f"Compliance requirements: {', '.join(compliance)}")
    
    # Combine all parts
    if context_parts:
        return ". ".join(context_parts) + "."
    else:
        return "Cloud migration and modernization initiative."


def display_evaluation_results(result: Dict[str, Any], show_detailed: bool, show_phases: bool, show_recs: bool):
    """Display the evaluation results."""
    
    evaluation = result["evaluation_result"]
    metadata = result["metadata"]
    
    # Overall summary
    st.subheader("Evaluation Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Score", f"{evaluation.overall_score:.1f}/3.0")
    
    with col2:
        compliance_pct = evaluation.spec_compliance.overall_compliance_score * 100
        st.metric("Compliance", f"{compliance_pct:.0f}%")
    
    with col3:
        st.metric("Gaps Identified", len(evaluation.gaps))
    
    with col4:
        st.metric("Recommendations", len(evaluation.recommendations))
    
    # Phase scores visualization
    if show_phases:
        st.subheader("Phase Scores")
        
        # Create phase scores chart
        phases = list(evaluation.scorecard.keys())
        scores = list(evaluation.scorecard.values())
        
        fig = go.Figure(data=[
            go.Bar(
                x=[phase.value.title() for phase in phases],
                y=scores,
                marker_color=['#ff4444' if s < 1.5 else '#ffaa00' if s < 2.5 else '#44ff44' for s in scores],
                text=scores,
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Migration Phase Scores (0-3 scale)",
            yaxis=dict(range=[0, 3]),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Phase details
        for phase_eval in evaluation.phase_evaluations:
            with st.expander(f"{phase_eval.phase.value.title()} Phase Details"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Strengths:**")
                    for strength in phase_eval.strengths:
                        st.markdown(f"• {strength}")
                
                with col2:
                    st.markdown("**Areas for Improvement:**")
                    for weakness in phase_eval.weaknesses:
                        st.markdown(f"• {weakness}")
                
                if phase_eval.evidence:
                    st.markdown("**Evidence:**")
                    for evidence in phase_eval.evidence:
                        st.markdown(f"• {evidence}")
    
    # Gaps analysis
    if evaluation.gaps:
        st.subheader("Gap Analysis")
        
        # Group gaps by severity
        critical_gaps = [g for g in evaluation.gaps if g.severity == "critical"]
        high_gaps = [g for g in evaluation.gaps if g.severity == "high"]
        medium_gaps = [g for g in evaluation.gaps if g.severity == "medium"]
        low_gaps = [g for g in evaluation.gaps if g.severity == "low"]
        
        if critical_gaps:
            st.markdown("### Critical Gaps")
            for gap in critical_gaps:
                st.markdown(f"""
                <div class="critical-gap">
                    <strong>{gap.area}</strong><br>
                    {gap.description}<br>
                    <em>Impact: {gap.impact}</em>
                </div>
                """, unsafe_allow_html=True)
        
        if high_gaps:
            st.markdown("### High Priority Gaps")
            for gap in high_gaps:
                st.markdown(f"""
                <div class="high-gap">
                    <strong>{gap.area}</strong><br>
                    {gap.description}<br>
                    <em>Impact: {gap.impact}</em>
                </div>
                """, unsafe_allow_html=True)
        
        # Show medium and low gaps in expander
        if medium_gaps or low_gaps:
            with st.expander(f"Other Gaps ({len(medium_gaps + low_gaps)} items)"):
                for gap in medium_gaps + low_gaps:
                    st.markdown(f"**{gap.area}** ({gap.severity}): {gap.description}")
    
    # Recommendations
    if show_recs and evaluation.recommendations:
        st.subheader("Recommendations")
        
        # Group recommendations by priority
        critical_recs = [r for r in evaluation.recommendations if r.priority == "critical"]
        high_recs = [r for r in evaluation.recommendations if r.priority == "high"]
        medium_recs = [r for r in evaluation.recommendations if r.priority == "medium"]
        low_recs = [r for r in evaluation.recommendations if r.priority == "low"]
        
        if critical_recs:
            st.markdown("### Critical Recommendations")
            for rec in critical_recs:
                phase_str = f" ({rec.phase.value})" if rec.phase else ""
                st.markdown(f"""
                <div class="recommendation">
                    <strong>{rec.title}{phase_str}</strong><br>
                    {rec.description}<br>
                    <em>Implementation effort: {rec.implementation_effort}</em>
                </div>
                """, unsafe_allow_html=True)
        
        if high_recs:
            st.markdown("### High Priority Recommendations")
            for rec in high_recs:
                phase_str = f" ({rec.phase.value})" if rec.phase else ""
                st.markdown(f"""
                <div class="recommendation">
                    <strong>{rec.title}{phase_str}</strong><br>
                    {rec.description}<br>
                    <em>Implementation effort: {rec.implementation_effort}</em>
                </div>
                """, unsafe_allow_html=True)
        
        # Show other recommendations in expander
        if medium_recs or low_recs:
            with st.expander(f"Additional Recommendations ({len(medium_recs + low_recs)} items)"):
                for rec in medium_recs + low_recs:
                    phase_str = f" ({rec.phase.value})" if rec.phase else ""
                    st.markdown(f"**{rec.title}{phase_str}** ({rec.priority}): {rec.description}")
    
    # Detailed analysis
    if show_detailed:
        with st.expander("Detailed Analysis"):
            st.markdown("### Document Information")
            st.json(metadata["document_info"])
            
            st.markdown("### Processing Information")
            st.json(metadata["processing_info"])
            
            st.markdown("### Compliance Details")
            st.markdown(f"**Compliant Areas:** {', '.join(evaluation.spec_compliance.compliant_areas)}")
            st.markdown(f"**Non-Compliant Areas:** {', '.join(evaluation.spec_compliance.non_compliant_areas)}")
            st.markdown(f"**Missing Elements:** {', '.join(evaluation.spec_compliance.missing_elements)}")
    
    # Export options
    st.subheader("Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export as YAML"):
            yaml_output = create_yaml_export(evaluation)
            st.download_button(
                label="Download YAML Report",
                data=yaml_output,
                file_name=f"evaluation_report_{uploaded_file.name}.yaml",
                mime="text/yaml"
            )
    
    with col2:
        if st.button("Export as JSON"):
            import json
            json_output = json.dumps(result, default=str, indent=2)
            st.download_button(
                label="Download JSON Report",
                data=json_output,
                file_name=f"evaluation_report_{uploaded_file.name}.json",
                mime="application/json"
            )


def create_yaml_export(evaluation) -> str:
    """Create YAML export of evaluation results."""
    
    export_data = {
        "evaluation_result": {
            "scorecard": {phase.value: score for phase, score in evaluation.scorecard.items()},
            "comments": {phase.value: comment for phase, comment in evaluation.comments.items()},
            "overall_score": evaluation.overall_score,
            "summary": evaluation.summary,
            "compliance": {
                "score": evaluation.spec_compliance.overall_compliance_score,
                "compliant_areas": evaluation.spec_compliance.compliant_areas,
                "non_compliant_areas": evaluation.spec_compliance.non_compliant_areas,
                "missing_elements": evaluation.spec_compliance.missing_elements
            },
            "gaps": [
                {
                    "area": gap.area,
                    "severity": gap.severity,
                    "description": gap.description,
                    "impact": gap.impact,
                    "phase": gap.phase.value if gap.phase else None
                }
                for gap in evaluation.gaps
            ],
            "recommendations": [
                {
                    "title": rec.title,
                    "description": rec.description,
                    "priority": rec.priority,
                    "phase": rec.phase.value if rec.phase else None,
                    "implementation_effort": rec.implementation_effort
                }
                for rec in evaluation.recommendations
            ]
        }
    }
    
    return yaml.dump(export_data, default_flow_style=False, sort_keys=False)


def display_sow_results(result, show_detailed_analysis, show_phase_breakdown, show_recommendations):
    """Display SOW evaluation results."""
    
    # Framework notice
    st.warning("**SOW Evaluation Framework** - This is a placeholder implementation. Actual evaluation logic will be added later.")
    
    # Overall Score
    overall_score = result.get('overall_score', 0)
    max_score = result.get('max_score', 9)  # 3 phases * 3 max score each
    percentage = (overall_score / max_score) * 100 if max_score > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Framework Score", f"{overall_score}/{max_score}", f"{percentage:.1f}%")
    
    with col2:
        st.metric("Status", "Framework Ready")
    
    with col3:
        st.metric("Phases Configured", len(result.get('phase_results', {})))
    
    # Phase Breakdown
    if show_phase_breakdown and result.get('phase_results'):
        st.subheader("Framework Phase Structure")
        
        phase_data = []
        for phase_name, phase_result in result['phase_results'].items():
            phase_data.append({
                'Phase': phase_name.replace('_', ' ').title(),
                'Score': phase_result.get('score', 0),
                'Max Score': 3,
                'Percentage': (phase_result.get('score', 0) / 3) * 100
            })
        
        # Create bar chart
        fig = px.bar(
            phase_data, 
            x='Phase', 
            y='Percentage',
            title='SOW Framework Phase Structure (Placeholder Data)',
            color='Percentage',
            color_continuous_scale='Blues',
            range_color=[0, 100]
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed phase results
        for phase_name, phase_result in result['phase_results'].items():
            with st.expander(f"{phase_name.replace('_', ' ').title()} Framework"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Framework Score", f"{phase_result.get('score', 0)}/3")
                    
                with col2:
                    phase_percentage = (phase_result.get('score', 0) / 3) * 100
                    st.metric("Readiness", f"{phase_percentage:.1f}%")
                
                if phase_result.get('feedback'):
                    st.markdown("**Framework Status:**")
                    st.markdown(phase_result['feedback'])
                
                if phase_result.get('strengths'):
                    st.markdown("**Framework Strengths:**")
                    for strength in phase_result['strengths']:
                        st.markdown(f"• {strength}")
                
                if phase_result.get('gaps'):
                    st.markdown("**Implementation Needed:**")
                    for gap in phase_result['gaps']:
                        st.markdown(f"• {gap}")
    
    # Key Findings
    if show_detailed_analysis and result.get('key_findings'):
        st.subheader("Framework Status")
        
        st.markdown("**Current State:**")
        for finding in result['key_findings']:
            st.markdown(f"• {finding}")
    
    # Recommendations
    if show_recommendations and result.get('recommendations'):
        st.subheader("Implementation Roadmap")
        
        for i, recommendation in enumerate(result['recommendations'], 1):
            st.markdown(f"**{i}. {recommendation.get('title', 'Recommendation')}**")
            st.markdown(recommendation.get('description', ''))
            
            if recommendation.get('priority'):
                priority_color = {
                    'High': 'High',
                    'Medium': 'Medium', 
                    'Low': 'Low'
                }.get(recommendation['priority'], 'Unknown')
                st.markdown(f"Priority: {priority_color}")
            
            st.markdown("---")
    
    # Export Options
    st.subheader("Framework Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Framework as YAML"):
            yaml_content = create_sow_yaml_export(result)
            st.download_button(
                label="Download Framework Report",
                data=yaml_content,
                file_name=f"sow_framework_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml",
                mime="text/yaml"
            )
    
    with col2:
        if st.button("Export Framework Summary"):
            summary = create_sow_summary_export(result)
            st.download_button(
                label="Download Framework Summary",
                data=summary,
                file_name=f"sow_framework_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )


def create_sow_yaml_export(result):
    """Create YAML export for SOW evaluation results."""
    export_data = {
        'sow_evaluation_report': {
            'timestamp': datetime.now().isoformat(),
            'overall_score': result.get('overall_score', 0),
            'max_score': result.get('max_score', 9),
            'percentage': (result.get('overall_score', 0) / result.get('max_score', 9)) * 100,
            'phase_results': result.get('phase_results', {}),
            'key_findings': result.get('key_findings', []),
            'risks': result.get('risks', []),
            'recommendations': result.get('recommendations', []),
            'quality_indicators': result.get('quality_indicators', {})
        }
    }
    return yaml.dump(export_data, default_flow_style=False, sort_keys=False)


def create_sow_summary_export(result):
    """Create text summary export for SOW evaluation results."""
    overall_score = result.get('overall_score', 0)
    max_score = result.get('max_score', 9)
    percentage = (overall_score / max_score) * 100 if max_score > 0 else 0
    
    summary = f"""SOW EVALUATION SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERALL RESULTS:
- Score: {overall_score:.1f}/{max_score} ({percentage:.1f}%)
- Quality Level: {"Excellent" if percentage >= 80 else "Good" if percentage >= 60 else "Needs Improvement" if percentage >= 40 else "Poor"}

PHASE BREAKDOWN:
"""
    
    for phase_name, phase_result in result.get('phase_results', {}).items():
        phase_score = phase_result.get('score', 0)
        phase_percentage = (phase_score / 3) * 100
        summary += f"- {phase_name.replace('_', ' ').title()}: {phase_score}/3 ({phase_percentage:.1f}%)\n"
    
    if result.get('key_findings'):
        summary += "\nKEY FINDINGS:\n"
        for finding in result['key_findings']:
            summary += f"- {finding}\n"
    
    if result.get('recommendations'):
        summary += "\nRECOMMENDATIONS:\n"
        for i, rec in enumerate(result['recommendations'], 1):
            summary += f"{i}. {rec.get('title', 'Recommendation')}\n"
            summary += f"   {rec.get('description', '')}\n"
    
    return summary


def display_proposal_generator_results(result, show_detailed_analysis, show_phase_breakdown, show_recommendations):
    """Display proposal generator results."""
    
    if not result.get("success"):
        st.error("Proposal generation failed!")
        if result.get("errors"):
            st.error("Errors: " + ", ".join(result["errors"]))
        if result.get("warnings"):
            st.warning("Warnings: " + ", ".join(result["warnings"]))
        return
    
    proposal_state = result.get("proposal_state")
    if not proposal_state:
        st.error("No proposal state found in results")
        return
    
    # Overall summary
    st.subheader("Proposal Generation Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        applications = proposal_state.get("applications", []) or proposal_state.get("classified_workloads", [])
        st.metric("Applications", len(applications))
    
    with col2:
        wave_groups = proposal_state.get("wave_groups", [])
        migration_waves = proposal_state.get("migration_waves", {})
        waves_count = len(wave_groups) if wave_groups else (len(migration_waves.get("waves", [])) if migration_waves else 0)
        st.metric("Migration Waves", waves_count)
    
    with col3:
        sprint_estimates = proposal_state.get("sprint_estimates", [])
        total_sprints = sum(est.get("total_sprints", 0) for est in sprint_estimates) if sprint_estimates else 0
        st.metric("Total Sprints", total_sprints)
    
    with col4:
        total_weeks = total_sprints * 2  # 2-week sprints
        st.metric("Timeline (weeks)", total_weeks)
    
    with col5:
        feedback_count = len(result.get("feedback_loops", []))
        st.metric("Optimisations", feedback_count, help="Number of feedback loops triggered for optimisation")
    
    # Show feedback loop information if any occurred
    if result.get("feedback_loops"):
        st.info(f"**Intelligent Optimisation Applied**: {result.get('iterations', 1)} iterations with {len(result['feedback_loops'])} feedback loops")
        
        with st.expander("View Optimisation Details"):
            st.markdown("**Feedback Loops Triggered:**")
            for loop in result["feedback_loops"]:
                if "wave_replan" in loop:
                    st.markdown("**Wave Replanning**: Modernisation bias detected refactor opportunities, replanned migration waves")
                elif "scope_update" in loop:
                    st.markdown("**Scope Update**: Complex architecture patterns detected, updated project scope")
                elif "strategy_reclassification" in loop:
                    st.markdown("**Strategy Optimisation**: High effort detected, reclassified to simpler migration strategies")
                else:
                    st.markdown(f"**{loop.replace('_', ' ').title()}**")
            
            st.markdown(f"**Final Version**: {result.get('iterations', 1)} (optimised through recursive analysis)")
    else:
        st.success("**Optimal Plan Generated**: No optimisation loops needed - plan was optimal on first pass")
    
    # Applications Analysis
    applications = proposal_state.get("applications", []) or proposal_state.get("classified_workloads", [])
    if show_detailed_analysis and applications:
        st.subheader("Application Portfolio Analysis")
        
        # Create applications dataframe for visualization
        app_data = []
        migration_strategies = proposal_state.get("migration_strategies", {})
        
        for app in applications:
            # Handle both object and dict formats
            app_name = app.get("name") if isinstance(app, dict) else getattr(app, "name", "Unknown")
            app_tech = app.get("technology_stack", []) if isinstance(app, dict) else getattr(app, "technology_stack", [])
            app_criticality = app.get("business_criticality", "Medium") if isinstance(app, dict) else getattr(app, "criticality", "Medium")
            app_users = app.get("estimated_users", 0) if isinstance(app, dict) else getattr(app, "estimated_users", 0)
            
            strategy = migration_strategies.get(app_name, "Unknown")
            
            app_data.append({
                "Application": app_name,
                "Technology": ", ".join(app_tech[:3]) + ("..." if len(app_tech) > 3 else "") if app_tech else "Unknown",
                "Criticality": str(app_criticality),
                "Strategy": str(strategy),
                "Users": app_users or 0
            })
        
        if app_data:
            df = pd.DataFrame(app_data)
            st.dataframe(df, use_container_width=True)
            
            # Strategy distribution chart
            if migration_strategies:
                strategy_counts = {}
                for strategy in migration_strategies.values():
                    strategy_name = str(strategy)
                    strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
                
                if strategy_counts:
                    fig = px.pie(
                        values=list(strategy_counts.values()),
                        names=list(strategy_counts.keys()),
                        title="Migration Strategy Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    # Wave Planning
    wave_groups = proposal_state.get("wave_groups", [])
    migration_waves = proposal_state.get("migration_waves", {})
    
    if show_phase_breakdown and (wave_groups or migration_waves):
        st.subheader("Migration Wave Planning")
        
        # Handle wave_groups format
        if wave_groups:
            for wave in wave_groups:
                wave_name = getattr(wave, "name", f"Wave {getattr(wave, 'wave_number', 'Unknown')}")
                with st.expander(f"Wave {getattr(wave, 'wave_number', 'Unknown')}: {wave_name}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Strategy:** {getattr(wave, 'strategy', 'Unknown')}")
                        st.markdown(f"**Duration:** {getattr(wave, 'estimated_duration_weeks', 'Unknown')} weeks")
                        st.markdown(f"**Risk Level:** {getattr(wave, 'risk_level', 'Unknown')}")
                    
                    with col2:
                        st.markdown("**Applications:**")
                        for app_name in getattr(wave, "applications", []):
                            st.markdown(f"• {app_name}")
                    
                    prerequisites = getattr(wave, "prerequisites", [])
                    if prerequisites:
                        st.markdown("**Prerequisites:**")
                        for prereq in prerequisites:
                            st.markdown(f"• {prereq}")
        
        # Handle migration_waves format
        elif migration_waves and migration_waves.get("waves"):
            for wave in migration_waves["waves"]:
                wave_name = wave.get("name", f"Wave {wave.get('wave_number', 'Unknown')}")
                with st.expander(f"Wave {wave.get('wave_number', 'Unknown')}: {wave_name}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Track:** {wave.get('track', 'Unknown')}")
                        st.markdown(f"**Duration:** {wave.get('duration_weeks', 'Unknown')} weeks")
                        st.markdown(f"**Risk Level:** {wave.get('risk_level', 'Unknown')}")
                    
                    with col2:
                        st.markdown("**Applications:**")
                        for app_name in wave.get("applications", []):
                            st.markdown(f"• {app_name}")
                    
                    success_criteria = wave.get("success_criteria", [])
                    if success_criteria:
                        st.markdown("**Success Criteria:**")
                        for criteria in success_criteria:
                            st.markdown(f"• {criteria}")
    
    # Architecture Recommendations
    architecture_recommendations = proposal_state.get("architecture_recommendations", [])
    if show_recommendations and architecture_recommendations:
        st.subheader("Architecture Recommendations")
        
        for rec in architecture_recommendations:
            # Handle both object and dict formats
            if isinstance(rec, dict):
                cloud_provider = rec.get("cloud_provider", "Unknown")
                services = rec.get("services", {})
                patterns = rec.get("patterns", [])
            else:
                cloud_provider = getattr(rec, "cloud_provider", "Unknown")
                services = getattr(rec, "services", {})
                patterns = getattr(rec, "patterns", [])
            
            with st.expander(f"{str(cloud_provider).upper()} Architecture"):
                if services:
                    st.markdown("**Recommended Services:**")
                    for service_type, service_name in services.items():
                        st.markdown(f"• **{service_type.title()}:** {service_name}")
                
                if patterns:
                    st.markdown("**Architecture Patterns:**")
                    for pattern in patterns:
                        st.markdown(f"• {pattern}")
    
    # GenAI Tools
    genai_tool_plans = proposal_state.get("genai_tool_plans", [])
    if genai_tool_plans:
        st.subheader("GenAI Tool Integration")
        
        for plan in genai_tool_plans:
            # Handle both object and dict formats
            if isinstance(plan, dict):
                tool_name = plan.get("tool", "Unknown Tool")
                use_cases = plan.get("use_cases", [])
                expected_benefits = plan.get("expected_benefits", [])
            else:
                tool_name = getattr(plan, "tool", "Unknown Tool")
                use_cases = getattr(plan, "use_cases", [])
                expected_benefits = getattr(plan, "expected_benefits", [])
            
            with st.expander(f"{str(tool_name).replace('_', ' ').title()}"):
                if use_cases:
                    st.markdown("**Use Cases:**")
                    for use_case in use_cases:
                        st.markdown(f"• {use_case}")
                
                if expected_benefits:
                    st.markdown("**Expected Benefits:**")
                    for benefit in expected_benefits:
                        st.markdown(f"• {benefit}")
    
    # Generated Proposal Content
    markdown_output = proposal_state.get("markdown_output")
    if markdown_output:
        st.subheader("Generated Proposal")
        
        # Show preview
        with st.expander("Preview Proposal Content"):
            preview_content = markdown_output[:2000] + "..." if len(markdown_output) > 2000 else markdown_output
            st.markdown(preview_content)
    
    # Export Options
    st.subheader("Export Proposal")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export as Markdown"):
            if markdown_output:
                st.download_button(
                    label="Download Markdown",
                    data=markdown_output,
                    file_name=f"migration_proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            else:
                st.error("No markdown content available")
    
    with col2:
        if st.button("Export as YAML"):
            yaml_content = create_proposal_generator_yaml_export(result)
            st.download_button(
                label="Download YAML",
                data=yaml_content,
                file_name=f"proposal_generator_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml",
                mime="text/yaml"
            )
    
    with col3:
        if st.button("Export as JSON"):
            import json
            # Convert proposal state to dict for JSON serialization
            proposal_dict = {
                "success": result.get("success"),
                "applications": applications,
                "wave_groups": wave_groups,
                "migration_waves": migration_waves,
                "feedback_loops": result.get("feedback_loops", []),
                "iterations": result.get("iterations", 1),
                "optimisation_applied": len(result.get("feedback_loops", [])) > 0
            }
            
            json_content = json.dumps(proposal_dict, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=json_content,
                file_name=f"proposal_generator_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


def create_proposal_generator_yaml_export(result):
    """Create YAML export for proposal generator results."""
    export_data = {
        'proposal_generator_report': {
            'timestamp': datetime.now().isoformat(),
            'title': result.get('title', 'Untitled Proposal'),
            'description': result.get('description', 'No description provided'),
            'content': result.get('content', 'No proposal content provided')
        }
    }
    return yaml.dump(export_data, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    main() 