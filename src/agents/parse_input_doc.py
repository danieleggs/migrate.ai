from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from ..models.evaluation import GraphState, ParsedDocument
from ..utils.document_parser import DocumentParser


class ParseInputDocAgent:
    """Agent responsible for parsing input documents and extracting structured information."""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a document analysis expert. Your task is to analyze the parsed document content and enhance the section extraction.

The document has already been parsed and basic sections identified. Your job is to:
1. Review the existing sections and improve their boundaries if needed
2. Identify any missing important sections
3. Extract key metadata about the document
4. Provide a summary of the document's purpose and scope

Focus on sections relevant to migration projects, technology assessments, and project proposals."""),
            ("human", """Document Type: {document_type}
Filename: {filename}
Content Length: {content_length} characters

Existing Sections:
{existing_sections}

Full Content (first 2000 chars):
{content_preview}

Please analyze this document and provide:
1. Enhanced section mapping (if improvements needed)
2. Key themes and topics identified
3. Document purpose and scope
4. Any migration-related content indicators

Respond in JSON format with the following structure:
{{
    "enhanced_sections": {{"section_name": "section_content"}},
    "key_themes": ["theme1", "theme2"],
    "document_purpose": "brief description",
    "migration_indicators": ["indicator1", "indicator2"],
    "quality_assessment": "assessment of document completeness and clarity"
}}""")
        ])
    
    def __call__(self, state: GraphState) -> Dict[str, Any]:
        """Process the document parsing step."""
        try:
            if not state.parsed_document:
                return {"error": "No parsed document found in state"}
            
            doc = state.parsed_document
            
            # Prepare prompt inputs
            existing_sections = "\n".join([
                f"- {name}: {content[:200]}..." 
                for name, content in doc.sections.items()
            ])
            
            content_preview = doc.content[:2000] if len(doc.content) > 2000 else doc.content
            
            # Get LLM analysis
            response = self.llm.invoke(
                self.prompt.format_messages(
                    document_type=doc.document_type.value,
                    filename=doc.metadata.get("filename", "unknown"),
                    content_length=len(doc.content),
                    existing_sections=existing_sections,
                    content_preview=content_preview
                )
            )
            
            # Parse LLM response (assuming it returns valid JSON)
            import json
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis = {
                    "enhanced_sections": doc.sections,
                    "key_themes": [],
                    "document_purpose": "Unable to determine",
                    "migration_indicators": [],
                    "quality_assessment": "Analysis failed"
                }
            
            # Update document with enhanced information
            enhanced_doc = ParsedDocument(
                content=doc.content,
                document_type=doc.document_type,
                sections={**doc.sections, **analysis.get("enhanced_sections", {})},
                metadata={
                    **doc.metadata,
                    "key_themes": analysis.get("key_themes", []),
                    "document_purpose": analysis.get("document_purpose", ""),
                    "migration_indicators": analysis.get("migration_indicators", []),
                    "quality_assessment": analysis.get("quality_assessment", "")
                }
            )
            
            return {"parsed_document": enhanced_doc}
            
        except Exception as e:
            return {"error": f"Error in ParseInputDoc agent: {str(e)}"}


def parse_input_doc_node(state: GraphState) -> Dict[str, Any]:
    """LangGraph node function for document parsing."""
    from langchain_openai import ChatOpenAI
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = ParseInputDocAgent(llm)
    
    result = agent(state)
    
    if "error" in result:
        return {"error": result["error"]}
    else:
        return {"parsed_document": result["parsed_document"]} 