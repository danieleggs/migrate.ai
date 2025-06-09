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

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Modernize.AI Pre-Sales Evaluator",
    page_icon="🔧",
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
    
    # Header
    st.markdown('<h1 class="main-header">Pre-Sales Document Evaluator</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ## Migration-Focused Document Evaluation Tool
    
    Choose from different evaluation types to assess your documents:
    - **Migration Proposals**: Full evaluation against Modernize.AI specification
    - **Statement of Work**: Framework for SOW evaluation (logic to be implemented)
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
            type=['pdf', 'docx', 'txt', 'md'],
            help="Upload your document for evaluation"
        )
        
        if uploaded_file:
            st.success(f"File uploaded: {uploaded_file.name}")
            st.info(f"File size: {len(uploaded_file.getvalue())} bytes")
        
        st.markdown("---")
        
        # Evaluation options (only show if file is uploaded)
        if uploaded_file:
            st.subheader("Display Options")
            show_detailed_analysis = st.checkbox("Show detailed analysis", value=True)
            show_phase_breakdown = st.checkbox("Show phase breakdown", value=True)
            show_recommendations = st.checkbox("Show recommendations", value=True)
        else:
            show_detailed_analysis = True
            show_phase_breakdown = True
            show_recommendations = True
    
    # Main content area - only show evaluation if file is uploaded
    if uploaded_file is not None:
        run_evaluation(uploaded_file, selected_eval_type, selected_config, show_detailed_analysis, show_phase_breakdown, show_recommendations)
    else:
        # Blank right pane with just a simple message
        st.markdown("### Upload a document to begin evaluation")
        st.markdown("Select an evaluation type from the sidebar and upload your document to get started.")


def run_evaluation(uploaded_file, eval_type, config, show_detailed_analysis, show_phase_breakdown, show_recommendations):
    """Run the evaluation process based on the selected evaluation type."""
    
    st.subheader(f"{config.name}: {uploaded_file.name}")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Get file content
        file_content = uploaded_file.getvalue()
        
        if not file_content:
            st.error("No file content detected!")
            return
        
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
            
            # Display results
            if result["success"]:
                display_evaluation_results(result, show_detailed_analysis, show_phase_breakdown, show_recommendations)
            else:
                st.error(f"Evaluation failed: {result['error']}")
                if result.get("partial_results"):
                    st.subheader("Partial Results")
                    st.json(result["partial_results"])
        
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
            
            # Display SOW-specific results
            display_sow_results(result, show_detailed_analysis, show_phase_breakdown, show_recommendations)
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        progress_bar.empty()
        status_text.empty()


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


if __name__ == "__main__":
    main() 