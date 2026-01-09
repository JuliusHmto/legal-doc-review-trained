"""
Legal Document Review System - Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============ Document Schemas ============

class DocumentCreate(BaseModel):
    """Schema for uploading a document."""
    filename: str
    file_type: str
    content: str


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    filename: str
    file_type: Optional[str]
    content: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    id: UUID
    filename: str
    message: str
    file_type: str


# ============ Training Module Schemas ============

class ClauseAnalysis(BaseModel):
    """Individual clause analysis."""
    clause_title: str
    clause_text: str
    category: str  # e.g., "Employment Terms", "Liability", "Payment"
    key_points: List[str]
    potential_issues: List[str]
    relevant_laws: List[str]


class TrainingModuleContent(BaseModel):
    """Structured training module content."""
    document_type: str  # e.g., "Employment Contract", "Service Agreement"
    summary: str
    key_parties: List[str]
    effective_date: Optional[str]
    clauses: List[ClauseAnalysis]
    overall_assessment: str
    applicable_laws: List[str]


class TrainingModuleResponse(BaseModel):
    """Response for training module."""
    id: UUID
    document_id: UUID
    module_content: Dict[str, Any]
    summary: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Review Schemas ============

class ComplianceIssue(BaseModel):
    """Individual compliance issue."""
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    category: str
    description: str
    clause_reference: Optional[str]
    law_reference: str
    recommendation: str


class ReviewRequest(BaseModel):
    """Request for document review."""
    focus_areas: Optional[List[str]] = None  # e.g., ["employment", "data_protection"]


class ReviewResponse(BaseModel):
    """Full compliance review response."""
    id: UUID
    document_id: UUID
    compliance_score: int = Field(..., ge=0, le=100)
    issues: List[ComplianceIssue]
    recommendations: List[str]
    law_references: List[Dict[str, str]]
    reviewed_at: datetime
    
    class Config:
        from_attributes = True


class ReviewSummary(BaseModel):
    """Brief review summary."""
    document_id: UUID
    compliance_score: int
    total_issues: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    status: str  # "COMPLIANT", "NEEDS_REVIEW", "NON_COMPLIANT"

class HistoryItem(BaseModel):
    """Combined review and document info for history list."""
    review_id: UUID
    document_id: UUID
    filename: str
    compliance_score: int
    reviewed_at: datetime
    status: str

    class Config:
        from_attributes = True

# ============ RAG Schemas ============

class EmbeddingCreate(BaseModel):
    """Schema for creating embeddings."""
    module_id: UUID
    chunk_text: str
    embedding: List[float]


class SearchResult(BaseModel):
    """RAG search result."""
    chunk_text: str
    similarity_score: float
    module_id: UUID


# ============ NDA Cleanup Schemas ============

class CleanupIssue(BaseModel):
    """Individual cleanup issue found in the document."""
    type: str = Field(..., description="Type of issue: terminology, deletion, formatting, party_label, arbitration, signature")
    original_text: str = Field(..., description="The original problematic text")
    location: str = Field(..., description="Location in document (e.g., Clause 2.1)")
    rule: str = Field(..., description="The cleanup rule that was violated")


class CleanupOpenItem(BaseModel):
    """Placeholder item that needs manual review."""
    placeholder: str = Field(..., description="The placeholder used (e.g., [NAME], [DATE])")
    context: str = Field(..., description="Context about what information is needed")


class CleanupStats(BaseModel):
    """Statistics about the cleanup operation."""
    total_issues: int
    total_open_items: int
    total_changes: int
    issue_types: Dict[str, int] = Field(default_factory=dict)


class CleanupResponse(BaseModel):
    """Full response from NDA cleanup operation."""
    cleaned_indonesian: str = Field(..., description="Cleaned Indonesian text")
    cleaned_english: str = Field(..., description="Cleaned English text")
    change_summary: List[str] = Field(default_factory=list, description="List of changes made")
    open_items: List[CleanupOpenItem] = Field(default_factory=list)
    issues: List[CleanupIssue] = Field(default_factory=list)
    stats: Optional[CleanupStats] = None


class CleanupResultResponse(BaseModel):
    """Database response model for cleanup results."""
    id: UUID
    document_id: UUID
    original_content: Optional[str]
    cleaned_indonesian: Optional[str]
    cleaned_english: Optional[str]
    change_summary: Optional[List[str]]
    open_items: Optional[List[Dict[str, Any]]]
    issues: Optional[List[Dict[str, Any]]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CleanupQuickAnalysis(BaseModel):
    """Quick analysis result before full cleanup."""
    has_tracked_changes: bool = False
    has_terminology_issues: bool = False
    has_party_label_issues: bool = False
    has_arbitration_clause: bool = False
    has_signature_issues: bool = False
    summary: str = ""
    estimated_issue_count: int = 0
