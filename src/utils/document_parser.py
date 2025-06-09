import io
import re
from typing import Dict, Optional
from pathlib import Path

import PyPDF2
from docx import Document

from ..models.evaluation import DocumentType, ParsedDocument


class DocumentParser:
    """Utility class for parsing various document formats."""
    
    @staticmethod
    def parse_document(file_content: bytes, filename: str) -> ParsedDocument:
        """Parse document based on file extension."""
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return DocumentParser._parse_pdf(file_content, filename)
        elif extension == '.docx':
            return DocumentParser._parse_docx(file_content, filename)
        elif extension in ['.txt', '.md']:
            return DocumentParser._parse_text(file_content, filename)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    @staticmethod
    def _parse_pdf(file_content: bytes, filename: str) -> ParsedDocument:
        """Parse PDF document."""
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            content = ""
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
            
            sections = DocumentParser._extract_sections(content)
            document_type = DocumentParser._detect_document_type(content)
            
            return ParsedDocument(
                content=content,
                document_type=document_type,
                sections=sections,
                metadata={
                    "filename": filename,
                    "pages": str(len(pdf_reader.pages)),
                    "format": "pdf"
                }
            )
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    @staticmethod
    def _parse_docx(file_content: bytes, filename: str) -> ParsedDocument:
        """Parse DOCX document."""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            
            # Also extract from tables
            table_content = ""
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            table_content += cell_text + " "
                    table_content += "\n"
            
            if table_content:
                content += "\n" + table_content
            
            sections = DocumentParser._extract_sections(content)
            document_type = DocumentParser._detect_document_type(content)
            
            return ParsedDocument(
                content=content,
                document_type=document_type,
                sections=sections,
                metadata={
                    "filename": filename,
                    "paragraphs": str(len(doc.paragraphs)),
                    "tables": str(len(doc.tables)),
                    "format": "docx"
                }
            )
        except Exception as e:
            raise ValueError(f"Error parsing DOCX: {str(e)}")
    
    @staticmethod
    def _parse_text(file_content: bytes, filename: str) -> ParsedDocument:
        """Parse text document."""
        try:
            content = file_content.decode('utf-8')
            sections = DocumentParser._extract_sections(content)
            document_type = DocumentParser._detect_document_type(content)
            
            return ParsedDocument(
                content=content,
                document_type=document_type,
                sections=sections,
                metadata={
                    "filename": filename,
                    "lines": str(len(content.split('\n'))),
                    "format": "text"
                }
            )
        except Exception as e:
            raise ValueError(f"Error parsing text file: {str(e)}")
    
    @staticmethod
    def _extract_sections(content: str) -> Dict[str, str]:
        """Extract sections from document content."""
        sections = {}
        
        # Common section patterns
        section_patterns = [
            r'(?i)^(executive summary|summary)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
            r'(?i)^(introduction|overview)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
            r'(?i)^(approach|methodology)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
            r'(?i)^(solution|proposed solution)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
            r'(?i)^(timeline|schedule|project timeline)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
            r'(?i)^(team|resources|staffing)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
            r'(?i)^(technology|technical approach)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
            r'(?i)^(migration|migration approach)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
            r'(?i)^(assessment|analysis)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
            r'(?i)^(operations|operational support)[\s:]*\n(.*?)(?=\n\s*[A-Z][^a-z]*\n|\Z)',
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                section_name = match.group(1).lower().strip()
                section_content = match.group(2).strip()
                if section_content:
                    sections[section_name] = section_content
        
        return sections
    
    @staticmethod
    def _detect_document_type(content: str) -> DocumentType:
        """Detect document type based on content."""
        content_lower = content.lower()
        
        # RFP indicators
        rfp_indicators = [
            'request for proposal', 'rfp', 'request for quotation', 'rfq',
            'invitation to tender', 'itt', 'statement of work', 'sow'
        ]
        
        # Proposal indicators
        proposal_indicators = [
            'proposal', 'response to rfp', 'technical proposal',
            'commercial proposal', 'bid response'
        ]
        
        # Response indicators
        response_indicators = [
            'response', 'reply', 'submission', 'tender response'
        ]
        
        if any(indicator in content_lower for indicator in rfp_indicators):
            return DocumentType.RFP
        elif any(indicator in content_lower for indicator in proposal_indicators):
            return DocumentType.PROPOSAL
        elif any(indicator in content_lower for indicator in response_indicators):
            return DocumentType.RESPONSE
        else:
            return DocumentType.OTHER 