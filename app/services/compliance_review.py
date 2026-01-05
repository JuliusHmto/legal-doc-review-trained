"""
Legal Document Review System - Compliance Review Service
Performs Indonesian law compliance analysis using OpenAI and RAG.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
import json
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.rag_service import RAGService
from app.knowledge.indonesian_law import (
    COMPLIANCE_REVIEW_SYSTEM_PROMPT,
    COMPLIANCE_REVIEW_PROMPT,
    get_law_context,
    INDONESIAN_LAW_CATEGORIES
)

settings = get_settings()


class ComplianceReviewService:
    """Service for performing Indonesian law compliance review."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.rag_service = RAGService()
    
    async def perform_review(
        self,
        db: AsyncSession,
        document_content: str,
        training_module: Dict[str, Any],
        module_id: UUID,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive compliance review.
        
        Args:
            db: Database session
            document_content: Original document text
            training_module: Generated training module
            module_id: ID of the training module for RAG search
            focus_areas: Optional list of law categories to focus on
            
        Returns:
            Compliance review result
        """
        # Get relevant context from RAG
        rag_context = await self._get_rag_context(db, document_content, module_id)
        
        # Get Indonesian law context
        law_context = get_law_context(focus_areas)
        
        # Prepare the review prompt
        prompt = COMPLIANCE_REVIEW_PROMPT.format(
            document_content=document_content[:10000],  # Limit content to avoid token limits
            training_module=json.dumps(training_module, indent=2)[:5000],
            rag_context=rag_context + "\n\n" + law_context
        )
        
        # Call OpenAI for compliance review
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": COMPLIANCE_REVIEW_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_completion_tokens=16000,
            response_format={"type": "json_object"}
        )
        
        review_result = json.loads(response.choices[0].message.content)
        
        # Process and validate the result
        return self._process_review_result(review_result)
    
    async def _get_rag_context(
        self, 
        db: AsyncSession, 
        query: str, 
        module_id: UUID
    ) -> str:
        """Retrieve relevant context from RAG."""
        # Search for relevant chunks
        results = await self.rag_service.search_by_module(
            db, 
            module_id, 
            query[:1000],  # Use first 1000 chars as query
            limit=5
        )
        
        if not results:
            # If no results from specific module, search globally
            results = await self.rag_service.search_similar(
                db,
                query[:500],
                limit=3,
                similarity_threshold=0.5
            )
        
        context_parts = []
        for result in results:
            context_parts.append(result['chunk_text'])
        
        return "\n\n---\n\n".join(context_parts) if context_parts else "No additional context available."
    
    def _process_review_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate the review result."""
        # Ensure compliance score is valid
        score = result.get("compliance_score", 50)
        if not isinstance(score, int) or score < 0 or score > 100:
            score = 50
        
        # Determine status if not provided
        if "status" not in result:
            if score >= 70:
                result["status"] = "COMPLIANT"
            elif score >= 50:
                result["status"] = "NEEDS_REVIEW"
            else:
                result["status"] = "NON_COMPLIANT"
        
        # Ensure issues is a list
        if "issues" not in result or not isinstance(result["issues"], list):
            result["issues"] = []
        
        # Process each issue
        for issue in result["issues"]:
            # Ensure severity is valid
            if issue.get("severity") not in ["HIGH", "MEDIUM", "LOW"]:
                issue["severity"] = "MEDIUM"
        
        # Count issues by severity
        result["issue_counts"] = {
            "high": sum(1 for i in result["issues"] if i.get("severity") == "HIGH"),
            "medium": sum(1 for i in result["issues"] if i.get("severity") == "MEDIUM"),
            "low": sum(1 for i in result["issues"] if i.get("severity") == "LOW")
        }
        
        result["compliance_score"] = score
        
        return result
    
    async def quick_review(
        self,
        document_content: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform a quick compliance review without RAG context.
        Useful for initial assessment.
        """
        law_context = get_law_context(focus_areas)
        
        prompt = f"""
Perform a quick compliance review of this document against Indonesian law.

Document Content:
{document_content[:8000]}

Indonesian Law Context:
{law_context}

Respond with JSON containing:
- compliance_score (0-100)
- status (COMPLIANT, NEEDS_REVIEW, NON_COMPLIANT)
- key_issues (list of main issues)
- applicable_laws (list of relevant Indonesian laws)
- quick_recommendations (list of immediate recommendations)
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": COMPLIANCE_REVIEW_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_completion_tokens=8000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def get_available_categories(self) -> Dict[str, str]:
        """Get available law categories for focus areas."""
        return {
            key: info["name"] 
            for key, info in INDONESIAN_LAW_CATEGORIES.items()
        }
