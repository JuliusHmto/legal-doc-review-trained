"""
Legal Document Review System - Training Module Generator
Creates structured training modules from document content using OpenAI.
"""
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from app.config import get_settings
from app.knowledge.indonesian_law import TRAINING_MODULE_PROMPT

settings = get_settings()


class TrainingModuleGenerator:
    """Service for generating training modules from documents."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def generate_module(
        self, 
        document_content: str, 
        filename: str
    ) -> Dict[str, Any]:
        """
        Generate a structured training module from document content.
        
        Args:
            document_content: Extracted text from the document
            filename: Original filename for context
            
        Returns:
            Structured training module as dictionary
        """
        prompt = f"""Analyze the following legal document and create a structured training module.

Document Filename: {filename}

Document Content:
{document_content[:15000]}  # Limit to avoid token limits

{TRAINING_MODULE_PROMPT}

Respond in valid JSON format only, no additional text."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert Indonesian legal analyst specializing in document review and compliance. 
Your task is to analyze legal documents and create comprehensive training modules that identify key clauses, 
potential issues, and relevant Indonesian laws. Always respond in valid JSON format."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_completion_tokens=16000,
            response_format={"type": "json_object"}
        )
        
        import json
        response_content = response.choices[0].message.content
        
        if not response_content:
            raise ValueError(f"Empty response from OpenAI. Finish reason: {response.choices[0].finish_reason}")
        
        try:
            module_content = json.loads(response_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OpenAI response as JSON: {str(e)}. Response: {response_content[:500]}")
        
        return module_content
    
    async def generate_summary(self, module_content: Dict[str, Any]) -> str:
        """Generate a brief summary of the training module."""
        summary_parts = []
        
        doc_type = module_content.get("document_type", "Unknown Document")
        summary_parts.append(f"Document Type: {doc_type}")
        
        if "key_parties" in module_content:
            parties = ", ".join(module_content["key_parties"][:3])
            summary_parts.append(f"Parties: {parties}")
        
        if "clauses" in module_content:
            num_clauses = len(module_content["clauses"])
            summary_parts.append(f"Contains {num_clauses} key clauses")
        
        if "potential_issues" in module_content:
            num_issues = len(module_content.get("potential_issues", []))
            if num_issues > 0:
                summary_parts.append(f"Identified {num_issues} potential issues")
        
        if "applicable_laws" in module_content:
            laws = module_content["applicable_laws"][:3]
            summary_parts.append(f"Relevant Laws: {', '.join(laws)}")
        
        return " | ".join(summary_parts)
    
    def extract_searchable_text(self, module_content: Dict[str, Any]) -> list[str]:
        """Extract text chunks from module for RAG indexing."""
        chunks = []
        
        # Add summary
        if "summary" in module_content:
            chunks.append(f"Document Summary: {module_content['summary']}")
        
        # Add overall assessment
        if "overall_assessment" in module_content:
            chunks.append(f"Overall Assessment: {module_content['overall_assessment']}")
        
        # Add each clause as a chunk
        for clause in module_content.get("clauses", []):
            clause_text = f"""
Clause: {clause.get('clause_title', 'Unknown')}
Category: {clause.get('category', 'General')}
Content: {clause.get('clause_text', '')}
Key Points: {', '.join(clause.get('key_points', []))}
Potential Issues: {', '.join(clause.get('potential_issues', []))}
Relevant Laws: {', '.join(clause.get('relevant_laws', []))}
"""
            chunks.append(clause_text.strip())
        
        # Add applicable laws
        if "applicable_laws" in module_content:
            laws_text = "Applicable Indonesian Laws: " + ", ".join(module_content["applicable_laws"])
            chunks.append(laws_text)
        
        return chunks
