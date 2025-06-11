import pytest
import json
from unittest.mock import Mock, patch
from src.models.proposal_generation import (
    DiscoveryInput, ProposalState, Application, WaveGroup, 
    MigrationStrategy, WorkloadComplexity, CloudProvider, GenAITool
)
from src.graph.proposal_generation_graph import ProposalGenerationOrchestrator
from src.agents.proposal_nodes import (
    parse_input_node, classify_workloads_node, generate_overview_node,
    wave_planning_node, migration_strategy_6rs_node
)


class TestProposalModels:
    """Test the Pydantic models for proposal generation."""
    
    def test_discovery_input_creation(self):
        """Test DiscoveryInput model creation."""
        discovery_data = {
            "source_type": "json",
            "raw_data": {"applications": []},
            "client_name": "Test Client",
            "project_name": "Test Migration"
        }
        
        discovery_input = DiscoveryInput(**discovery_data)
        
        assert discovery_input.source_type == "json"
        assert discovery_input.client_name == "Test Client"
        assert discovery_input.project_name == "Test Migration"
    
    def test_application_creation(self):
        """Test Application model creation."""
        app_data = {
            "name": "Customer Portal",
            "description": "Web-based customer portal",
            "technology_stack": ["Java", "Spring Boot", "MySQL"],
            "criticality": WorkloadComplexity.HIGH,
            "current_environment": "On-premises"
        }
        
        application = Application(**app_data)
        
        assert application.name == "Customer Portal"
        assert application.criticality == WorkloadComplexity.HIGH
        assert len(application.technology_stack) == 3
    
    def test_wave_group_creation(self):
        """Test WaveGroup model creation."""
        wave_data = {
            "wave_number": 1,
            "name": "Foundation Wave",
            "applications": ["App1", "App2"],
            "strategy": "rehost",
            "estimated_duration_weeks": 8,
            "risk_level": WorkloadComplexity.LOW
        }
        
        wave_group = WaveGroup(**wave_data)
        
        assert wave_group.wave_number == 1
        assert wave_group.name == "Foundation Wave"
        assert len(wave_group.applications) == 2
        assert wave_group.risk_level == WorkloadComplexity.LOW
    
    def test_proposal_state_initialization(self):
        """Test ProposalState initialization."""
        discovery_input = DiscoveryInput(
            source_type="manual",
            raw_data={"test": "data"},
            client_name="Test Client",
            project_name="Test Project"
        )
        
        state = ProposalState(discovery_input=discovery_input)
        
        assert state.discovery_input.client_name == "Test Client"
        assert len(state.applications) == 0
        assert len(state.wave_groups) == 0
        assert state.version == 1


class TestProposalNodes:
    """Test individual proposal generation nodes."""
    
    def test_parse_input_node_json(self):
        """Test parsing JSON input."""
        discovery_input = DiscoveryInput(
            source_type="json",
            raw_data={"applications": [{"name": "Test App"}]},
            client_name="Test Client",
            project_name="Test Project"
        )
        
        state = ProposalState(discovery_input=discovery_input)
        result = parse_input_node(state)
        
        assert "workload_classification" in result
    
    @patch('src.agents.proposal_nodes.llm')
    def test_classify_workloads_node(self, mock_llm):
        """Test workload classification node."""
        mock_response = Mock()
        mock_response.content = '''
        {
            "applications": [
                {
                    "name": "Customer Portal",
                    "description": "Web portal for customers",
                    "technology_stack": ["Java", "MySQL"],
                    "dependencies": [],
                    "criticality": "high",
                    "current_environment": "On-premises",
                    "data_classification": "internal",
                    "compliance_requirements": [],
                    "estimated_users": 1000,
                    "performance_requirements": "High availability"
                }
            ]
        }
        '''
        mock_llm.invoke.return_value = mock_response
        
        state = ProposalState()
        state.workload_classification = {"test": "data"}
        
        result = classify_workloads_node(state)
        
        assert "applications" in result
        assert len(result["applications"]) == 1
        assert result["applications"][0].name == "Customer Portal"
    
    @patch('src.agents.proposal_nodes.llm')
    def test_generate_overview_node(self, mock_llm):
        """Test overview generation node."""
        mock_response = Mock()
        mock_response.content = "# Executive Summary\n\nThis is a comprehensive migration proposal..."
        mock_llm.invoke.return_value = mock_response
        
        discovery_input = DiscoveryInput(
            source_type="manual",
            raw_data={},
            client_name="Acme Corp",
            project_name="Cloud Migration",
            business_context="Digital transformation"
        )
        
        app = Application(
            name="Test App",
            description="Test application",
            technology_stack=["Java"],
            criticality=WorkloadComplexity.MEDIUM,
            current_environment="On-premises"
        )
        
        state = ProposalState(
            discovery_input=discovery_input,
            applications=[app]
        )
        
        result = generate_overview_node(state)
        
        assert "overview_content" in result
        assert "proposal_sections" in result
        assert len(result["proposal_sections"]) == 1
    
    @patch('src.agents.proposal_nodes.llm')
    def test_wave_planning_node(self, mock_llm):
        """Test wave planning node."""
        mock_response = Mock()
        mock_response.content = '''
        {
            "waves": [
                {
                    "wave_number": 1,
                    "name": "Foundation Wave",
                    "applications": ["Test App"],
                    "strategy": "rehost",
                    "estimated_duration_weeks": 6,
                    "dependencies": [],
                    "risk_level": "low",
                    "prerequisites": ["Infrastructure setup"]
                }
            ]
        }
        '''
        mock_llm.invoke.return_value = mock_response
        
        app = Application(
            name="Test App",
            description="Test application",
            technology_stack=["Java"],
            criticality=WorkloadComplexity.LOW,
            current_environment="On-premises"
        )
        
        state = ProposalState(applications=[app])
        
        result = wave_planning_node(state)
        
        assert "wave_groups" in result
        assert len(result["wave_groups"]) == 1
        assert result["wave_groups"][0].wave_number == 1
        assert result["wave_groups"][0].name == "Foundation Wave"
    
    @patch('src.agents.proposal_nodes.llm')
    def test_migration_strategy_6rs_node(self, mock_llm):
        """Test 6R strategy classification node."""
        mock_response = Mock()
        mock_response.content = '''
        {
            "strategies": {
                "Test App": "replatform"
            }
        }
        '''
        mock_llm.invoke.return_value = mock_response
        
        app = Application(
            name="Test App",
            description="Test application",
            technology_stack=["Java"],
            criticality=WorkloadComplexity.MEDIUM,
            current_environment="On-premises"
        )
        
        state = ProposalState(applications=[app])
        
        result = migration_strategy_6rs_node(state)
        
        assert "migration_strategies" in result
        assert "Test App" in result["migration_strategies"]
        assert result["migration_strategies"]["Test App"] == MigrationStrategy.REPLATFORM


class TestProposalOrchestrator:
    """Test the main proposal generation orchestrator."""
    
    @patch('src.graph.proposal_generation_graph.ProposalGenerationOrchestrator.__init__')
    @patch('src.graph.proposal_generation_graph.ProposalGenerationOrchestrator.generate_proposal')
    def test_orchestrator_initialization(self, mock_generate, mock_init):
        """Test orchestrator initialization."""
        mock_init.return_value = None
        
        orchestrator = ProposalGenerationOrchestrator()
        
        mock_init.assert_called_once()
    
    def test_proposal_generation_success(self):
        """Test successful proposal generation."""
        discovery_data = {
            "source_type": "manual",
            "raw_data": {
                "applications": [
                    {
                        "name": "Test App",
                        "description": "Test application",
                        "technology_stack": ["Java"],
                        "criticality": "medium",
                        "current_environment": "On-premises"
                    }
                ]
            },
            "client_name": "Test Client",
            "project_name": "Test Migration",
            "contact_info": {},
            "business_context": "Test context"
        }
        
        # Mock the entire workflow
        with patch('src.graph.proposal_generation_graph.create_proposal_generation_graph') as mock_graph:
            mock_compiled_graph = Mock()
            mock_final_state = Mock()
            
            # Set up mock state
            mock_final_state.errors = []
            mock_final_state.warnings = []
            mock_final_state.applications = [Mock()]
            mock_final_state.wave_groups = [Mock()]
            mock_final_state.proposal_sections = [Mock()]
            mock_final_state.version = 1
            mock_final_state.feedback_loops = []
            mock_final_state.markdown_output = "# Test Proposal"
            mock_final_state.docx_path = "test.docx"
            mock_final_state.pdf_path = "test.pdf"
            
            mock_compiled_graph.invoke.return_value = mock_final_state
            mock_graph.return_value = mock_compiled_graph
            
            orchestrator = ProposalGenerationOrchestrator()
            result = orchestrator.generate_proposal(discovery_data)
            
            assert result["success"] is True
            assert "proposal_state" in result
            assert "outputs" in result
            assert "metadata" in result


class TestProposalWorkflow:
    """Test the complete proposal generation workflow."""
    
    def test_feedback_loop_detection(self):
        """Test feedback loop detection logic."""
        from src.graph.proposal_generation_graph import should_replan_waves, should_reclassify_strategies
        
        # Test wave replanning
        state = ProposalState()
        state.feedback_loops = ["modernisation_upgrade"]
        
        assert should_replan_waves(state) is True
        
        # Test strategy reclassification
        from src.models.proposal_generation import SprintEstimate
        
        state = ProposalState()
        high_effort_estimate = SprintEstimate(
            wave_number=1,
            total_sprints=25,  # High effort
            team_size=5,
            effort_breakdown={"migration": 20, "testing": 5}
        )
        state.sprint_estimates = [high_effort_estimate]
        
        assert should_reclassify_strategies(state) is True
    
    def test_proposal_quality_estimation(self):
        """Test proposal quality estimation."""
        from src.graph.proposal_generation_graph import estimate_proposal_quality
        from src.models.proposal_generation import ProposalSection
        
        state = ProposalState()
        
        # Add applications
        app = Application(
            name="Test App",
            description="Test",
            technology_stack=["Java"],
            criticality=WorkloadComplexity.MEDIUM,
            current_environment="On-premises"
        )
        state.applications = [app]
        
        # Add migration strategies
        state.migration_strategies = {"Test App": MigrationStrategy.REFACTOR}
        
        # Add proposal sections
        section = ProposalSection(
            section_number="1",
            title="Overview",
            content="This is a comprehensive overview section with detailed content."
        )
        state.proposal_sections = [section]
        
        # Add GenAI tool plans
        from src.models.proposal_generation import GenAIToolPlan
        tool_plan = GenAIToolPlan(
            tool=GenAITool.GITHUB_COPILOT,
            use_cases=["Code generation"],
            phases=["migration"],
            expected_benefits=["Faster development"],
            implementation_notes="Integrate with workflow"
        )
        state.genai_tool_plans = [tool_plan]
        
        quality_metrics = estimate_proposal_quality(state)
        
        assert "completeness_score" in quality_metrics
        assert "modernisation_score" in quality_metrics
        assert "automation_score" in quality_metrics
        assert "overall_score" in quality_metrics
        
        # Should have good modernization score (refactor strategy)
        assert quality_metrics["modernisation_score"] == 1.0


class TestErrorHandling:
    """Test error handling in proposal generation."""
    
    def test_invalid_discovery_input(self):
        """Test handling of invalid discovery input."""
        with pytest.raises(Exception):
            # Missing required fields
            DiscoveryInput(source_type="json")
    
    def test_node_error_handling(self):
        """Test error handling in individual nodes."""
        from src.agents.proposal_nodes import parse_input_node
        
        # Test with invalid state
        state = ProposalState()  # No discovery input
        
        result = parse_input_node(state)
        
        # Should handle gracefully and return errors
        assert "errors" in result or result is not None
    
    def test_llm_response_parsing_error(self):
        """Test handling of invalid LLM responses."""
        with patch('src.agents.proposal_nodes.llm') as mock_llm:
            mock_response = Mock()
            mock_response.content = "Invalid JSON response"
            mock_llm.invoke.return_value = mock_response
            
            state = ProposalState()
            state.workload_classification = {"test": "data"}
            
            result = classify_workloads_node(state)
            
            # Should handle parsing errors gracefully
            assert "applications" in result
            # Should return empty list as fallback
            assert len(result["applications"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 