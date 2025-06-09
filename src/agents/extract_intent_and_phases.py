import time
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import GraphState, PhaseContent, MigrationPhase


class IntentAndPhaseExtractor:
    """Agent to extract intent and map content to migration phases."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = self._create_prompt()
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create the extraction prompt."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a migration expert. Analyze the document and map it to the three migration stages: Strategise and Plan, Migrate and Modernise, and Manage and Optimise.

STAGE DEFINITIONS:
- STRATEGISE_AND_PLAN: Discovery, assessment, strategic planning, business case development, technical architecture design, team enablement, capability preparation
- MIGRATE_AND_MODERNISE: Migration execution, automated tools, AI-assisted modernisation, data migration, validation, cutover activities, dual-track approach
- MANAGE_AND_OPTIMISE: Post-migration operations, monitoring, cost optimisation, performance tuning, security enhancement, innovation enablement, continuous improvement

For each stage, extract:
1. Relevant content from the document
2. Key points that relate to that stage
3. Confidence score (0.0-1.0) for how well the content addresses that stage

Focus on identifying concrete evidence of activities, tools, approaches, and outcomes for each stage."""),
            ("human", """Document Content: {content}

Document Type: {document_type}

Please analyze this document and extract content relevant to each migration stage.

IMPORTANT: Respond with ONLY valid JSON in the exact format below. Do not include any markdown formatting, explanations, or additional text.

{{
    "strategise_and_plan": {{
        "relevant_content": "extracted content relevant to strategise and plan stage",
        "key_points": ["point1", "point2", "point3"],
        "confidence_score": 0.8
    }},
    "migrate_and_modernise": {{
        "relevant_content": "extracted content relevant to migrate and modernise stage", 
        "key_points": ["point1", "point2", "point3"],
        "confidence_score": 0.5
    }},
    "manage_and_optimise": {{
        "relevant_content": "extracted content relevant to manage and optimise stage",
        "key_points": ["point1", "point2", "point3"], 
        "confidence_score": 0.2
    }},
    "overall_intent": "primary intent/purpose of the document",
    "phase": "strategise_and_plan",
    "document_focus": "which stage this document primarily focuses on"
}}""")
        ])

    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """Extract phase-specific content from the document."""
        try:
            # Add small delay to avoid rate limiting
            time.sleep(1)
            
            if not state.parsed_document:
                return {"error": "No parsed document found in state"}
            
            doc = state.parsed_document
            
            # Prepare sections summary
            sections_summary = "\n".join([
                f"- {name}: {content[:300]}..." if len(content) > 300 else f"- {name}: {content}"
                for name, content in doc.sections.items()
            ])
            
            # Get themes and indicators from metadata
            themes = doc.metadata.get("key_themes", [])
            indicators = doc.metadata.get("migration_indicators", [])
            
            # Get LLM analysis
            response = self.llm.invoke(
                self.prompt.format_messages(
                    content=doc.content[:2000],  # Reduced from 4000 to 2000 for faster processing
                    document_type=doc.document_type.value
                )
            )
            
            # Parse LLM response
            import json
            import re
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # Try to extract JSON from the response if it's wrapped in markdown or other text
                try:
                    # Look for JSON block in markdown
                    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response.content, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group(1))
                    else:
                        # Look for any JSON-like structure
                        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                        if json_match:
                            analysis = json.loads(json_match.group(0))
                        else:
                            raise json.JSONDecodeError("No JSON found", response.content, 0)
                except json.JSONDecodeError:
                    # Fallback: create a basic analysis based on content keywords
                    content_lower = doc.content.lower()
                    analysis = {
                        "strategise_and_plan": {
                            "relevant_content": "Assessment and planning content detected" if any(word in content_lower for word in ["assess", "plan", "strategy", "business case", "discovery"]) else "No relevant content identified",
                            "key_points": ["Content analysis based on keywords"],
                            "confidence_score": 0.7 if any(word in content_lower for word in ["assess", "plan", "strategy"]) else 0.1
                        },
                        "migrate_and_modernise": {
                            "relevant_content": "Migration content detected" if any(word in content_lower for word in ["migrate", "migration", "modernise", "deploy", "cutover"]) else "No relevant content identified",
                            "key_points": ["Content analysis based on keywords"],
                            "confidence_score": 0.7 if any(word in content_lower for word in ["migrate", "migration", "modernise"]) else 0.1
                        },
                        "manage_and_optimise": {
                            "relevant_content": "Operations content detected" if any(word in content_lower for word in ["monitor", "optimise", "operate", "manage", "performance"]) else "No relevant content identified",
                            "key_points": ["Content analysis based on keywords"],
                            "confidence_score": 0.7 if any(word in content_lower for word in ["monitor", "optimise", "operate"]) else 0.1
                        },
                        "overall_intent": "Document analysis (fallback mode)",
                        "phase": "strategise_and_plan",
                        "document_focus": "Unable to determine from LLM response"
                    }
            
            # Convert to PhaseContent objects
            phase_contents = []
            for stage, content in analysis.items():
                if stage in ["strategise_and_plan", "migrate_and_modernise", "manage_and_optimise"]:
                    try:
                        phase = MigrationPhase(stage)
                        phase_content = PhaseContent(
                            phase=phase,
                            relevant_content=content["relevant_content"],
                            key_points=content.get("key_points", []),
                            confidence_score=float(content.get("confidence_score", 0.0))
                        )
                        phase_contents.append(phase_content)
                    except (ValueError, KeyError) as e:
                        # Skip invalid stage mappings
                        continue
            
            # Ensure all stages are represented (with empty content if necessary)
            existing_stages = {pc.phase for pc in phase_contents}
            for stage in MigrationPhase:
                if stage not in existing_stages:
                    phase_contents.append(PhaseContent(
                        phase=stage,
                        relevant_content="No relevant content identified",
                        key_points=[],
                        confidence_score=0.0
                    ))
            
            return {
                "phase_contents": phase_contents,
                "overall_analysis": analysis.get("overall_intent", "No intent identified")
            }
            
        except Exception as e:
            return {"error": f"Error in ExtractIntentAndPhases agent: {str(e)}"}


def extract_intent_and_phases_node(state: GraphState) -> Dict[str, Any]:
    """LangGraph node function for phase content extraction."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = IntentAndPhaseExtractor(llm)
    
    result = agent(state)
    
    if "error" in result:
        return {"error": result["error"]}
    else:
        updates = {"phase_contents": result["phase_contents"]}
        
        # Store additional analysis data if needed
        if state.parsed_document:
            # Create new metadata dict with additional data
            new_metadata = state.parsed_document.metadata.copy()
            new_metadata["overall_analysis"] = result.get("overall_analysis", "")
            
            # Create new ParsedDocument with updated metadata
            from src.models.evaluation import ParsedDocument
            updates["parsed_document"] = ParsedDocument(
                content=state.parsed_document.content,
                document_type=state.parsed_document.document_type,
                sections=state.parsed_document.sections,
                metadata=new_metadata
            )
        
        return updates 