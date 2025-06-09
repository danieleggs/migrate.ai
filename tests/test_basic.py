import pytest
import os
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models.evaluation import (
    MigrationPhase, DocumentType, ParsedDocument, 
    PhaseContent, PhaseEvaluation, GraphState
)
from src.utils.document_parser import DocumentParser


def test_migration_phase_enum():
    """Test MigrationPhase enum values."""
    assert MigrationPhase.STRATEGISE_AND_PLAN == "strategise_and_plan"
    assert MigrationPhase.MIGRATE_AND_MODERNISE == "migrate_and_modernise"
    assert MigrationPhase.MANAGE_AND_OPTIMISE == "manage_and_optimise"


def test_document_type_enum():
    """Test DocumentType enum values."""
    assert DocumentType.RFP == "rfp"
    assert DocumentType.PROPOSAL == "proposal"
    assert DocumentType.RESPONSE == "response"
    assert DocumentType.OTHER == "other"


def test_parsed_document_creation():
    """Test ParsedDocument model creation."""
    doc = ParsedDocument(
        content="Test content",
        document_type=DocumentType.PROPOSAL,
        sections={"intro": "Introduction section"},
        metadata={"author": "Test Author", "version": "1.0"}
    )
    
    assert doc.content == "Test content"
    assert doc.document_type == DocumentType.PROPOSAL
    assert doc.sections["intro"] == "Introduction section"
    assert doc.metadata["author"] == "Test Author"
    assert doc.metadata["version"] == "1.0"


def test_phase_content_creation():
    """Test PhaseContent model creation."""
    phase_content = PhaseContent(
        phase=MigrationPhase.STRATEGISE_AND_PLAN,
        relevant_content="Strategic planning content",
        key_points=["Point 1", "Point 2"],
        confidence_score=0.8
    )
    
    assert phase_content.phase == MigrationPhase.STRATEGISE_AND_PLAN
    assert phase_content.relevant_content == "Strategic planning content"
    assert len(phase_content.key_points) == 2
    assert phase_content.confidence_score == 0.8


def test_phase_evaluation_creation():
    """Test PhaseEvaluation model creation."""
    evaluation = PhaseEvaluation(
        phase=MigrationPhase.MIGRATE_AND_MODERNISE,
        score=2,
        criteria_met={"automation": True, "testing": False},
        strengths=["Good automation"],
        weaknesses=["Limited testing"],
        evidence=["Evidence 1", "Evidence 2"]
    )
    
    assert evaluation.phase == MigrationPhase.MIGRATE_AND_MODERNISE
    assert evaluation.score == 2
    assert evaluation.criteria_met["automation"] is True
    assert evaluation.criteria_met["testing"] is False


def test_graph_state_creation():
    """Test GraphState model creation."""
    state = GraphState()
    
    assert state.parsed_document is None
    assert len(state.phase_contents) == 0
    assert len(state.phase_evaluations) == 0
    assert state.spec_compliance is None
    assert len(state.gaps) == 0
    assert len(state.recommendations) == 0
    assert state.evaluation_result is None
    assert state.error is None


def test_document_parser_text_parsing():
    """Test DocumentParser text parsing functionality."""
    parser = DocumentParser()
    
    test_text = """
    # Strategic Planning
    This section covers our strategic approach to migration.
    
    ## Migration Execution
    Details about the migration process.
    
    ### Operations Management
    Post-migration operational considerations.
    """
    
    result = parser.parse_text(test_text)
    
    assert result.content == test_text
    assert result.document_type == DocumentType.OTHER
    assert len(result.sections) > 0


def test_document_type_detection():
    """Test document type detection logic."""
    parser = DocumentParser()
    
    # Test RFP detection
    rfp_content = "Request for Proposal: Cloud Migration Services"
    rfp_result = parser.parse_text(rfp_content)
    assert rfp_result.document_type == DocumentType.RFP
    
    # Test proposal detection
    proposal_content = "Technical Proposal for Migration Project"
    proposal_result = parser.parse_text(proposal_content)
    assert proposal_result.document_type == DocumentType.PROPOSAL


if __name__ == "__main__":
    pytest.main([__file__]) 