"""
Legal Document Review System - API Routes
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid

from app.database import get_db, Document, TrainingModule, ReviewResult, CleanupResult
from app.models.schemas import (
    DocumentUploadResponse, 
    TrainingModuleResponse, 
    ReviewResponse,
    ReviewRequest,
    ReviewSummary,
    HistoryItem,
    DocumentResponse,
    CleanupResultResponse
)
from app.services.document_processor import DocumentProcessor
from app.services.training_module import TrainingModuleGenerator
from app.services.rag_service import RAGService
from app.services.compliance_review import ComplianceReviewService
from app.services.nda_cleanup_service import NDACleanupService

router = APIRouter()

# Initialize services
doc_processor = DocumentProcessor()
module_gen = TrainingModuleGenerator()
rag_service = RAGService()
review_service = ComplianceReviewService()
cleanup_service = NDACleanupService()

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document and extract its content, then automatically run NDA cleanup analysis."""
    if not doc_processor.validate_file(file.filename):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    content_bytes = await file.read()
    file_path = await doc_processor.save_file(file.filename, content_bytes)
    
    try:
        text_content = await doc_processor.extract_text(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")
    finally:
        await doc_processor.cleanup_file(file_path)
    
    # Store document in database
    db_doc = Document(
        filename=file.filename,
        file_type=doc_processor.get_file_extension(file.filename),
        content=text_content
    )
    db.add(db_doc)
    await db.flush()
    
    # Automatically run NDA cleanup analysis
    try:
        cleanup_result = await cleanup_service.perform_cleanup(text_content)
        
        # Store cleanup result in database
        db_cleanup = CleanupResult(
            document_id=db_doc.id,
            original_content=text_content,
            cleaned_indonesian=cleanup_result.get("cleaned_indonesian", ""),
            cleaned_english=cleanup_result.get("cleaned_english", ""),
            change_summary=cleanup_result.get("change_summary", []),
            open_items=cleanup_result.get("open_items", []),
            issues=cleanup_result.get("issues", [])
        )
        db.add(db_cleanup)
        await db.flush()
    except Exception as e:
        # Log the error but don't fail the upload
        print(f"NDA cleanup analysis failed: {str(e)}")
    
    return DocumentUploadResponse(
        id=db_doc.id,
        filename=db_doc.filename,
        file_type=db_doc.file_type,
        message="Document uploaded and processed successfully"
    )

@router.post("/modules/create/{document_id}", response_model=TrainingModuleResponse)
async def create_training_module(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Generate a training module from an existing document and index it in RAG."""
    # Get document
    result = await db.execute(select(Document).where(Document.id == document_id))
    db_doc = result.scalar_one_or_none()
    
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if module already exists
    module_result = await db.execute(
        select(TrainingModule).where(TrainingModule.document_id == document_id)
    )
    existing_module = module_result.scalar_one_or_none()
    if existing_module:
        return existing_module

    # Generate module content using OpenAI
    try:
        module_content = await module_gen.generate_module(db_doc.content, db_doc.filename)
        summary = await module_gen.generate_summary(module_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate training module: {str(e)}")
    
    # Store training module
    db_module = TrainingModule(
        document_id=document_id,
        module_content=module_content,
        summary=summary
    )
    db.add(db_module)
    await db.flush()
    
    # Create and store embeddings for RAG
    chunks = module_gen.extract_searchable_text(module_content)
    try:
        await rag_service.store_embeddings(db, db_module.id, chunks)
    except Exception as e:
        # We don't fail the whole request if RAG fails, but we should log it
        print(f"RAG embedding failed: {str(e)}")
        
    return db_module

@router.get("/modules/{document_id}", response_model=TrainingModuleResponse)
async def get_training_module(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get training module for a document."""
    result = await db.execute(
        select(TrainingModule).where(TrainingModule.document_id == document_id)
    )
    db_module = result.scalar_one_or_none()
    
    if not db_module:
        raise HTTPException(status_code=404, detail="Training module not found for this document")
    
    return db_module

@router.post("/review/{document_id}", response_model=ReviewResponse)
async def perform_compliance_review(
    document_id: uuid.UUID,
    request: Optional[ReviewRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """Perform a compliance review against Indonesian law."""
    # Get document and module
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    db_doc = doc_result.scalar_one_or_none()
    
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    module_result = await db.execute(
        select(TrainingModule).where(TrainingModule.document_id == document_id)
    )
    db_module = module_result.scalar_one_or_none()
    
    if not db_module:
        raise HTTPException(status_code=400, detail="Training module must be created before review")
    
    # Perform review
    focus_areas = request.focus_areas if request else None
    
    try:
        review_result_data = await review_service.perform_review(
            db=db,
            document_content=db_doc.content,
            training_module=db_module.module_content,
            module_id=db_module.id,
            focus_areas=focus_areas
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance review failed: {str(e)}")
    
    # Store review result
    db_review = ReviewResult(
        document_id=document_id,
        compliance_score=review_result_data.get("compliance_score"),
        issues=review_result_data.get("issues"),
        recommendations=review_result_data.get("recommendations"),
        law_references=review_result_data.get("law_references")
    )
    db.add(db_review)
    await db.flush()
    
    # Convert result to response schema
    return db_review

@router.get("/review/{document_id}/report", response_model=ReviewResponse)
async def get_compliance_report(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the latest compliance report for a document."""
    result = await db.execute(
        select(ReviewResult)
        .where(ReviewResult.document_id == document_id)
        .order_by(ReviewResult.reviewed_at.desc())
        .limit(1)
    )
    db_review = result.scalar_one_or_none()
    
    if not db_review:
        raise HTTPException(status_code=404, detail="No review found for this document")
    
    return db_review

@router.get("/laws/categories")
async def get_law_categories():
    """Get available Indonesian law categories."""
    return review_service.get_available_categories()

@router.get("/history", response_model=List[HistoryItem])
async def get_review_history(db: AsyncSession = Depends(get_db)):
    """Get all past compliance reviews with document names."""
    query = (
        select(ReviewResult, Document.filename)
        .join(Document, ReviewResult.document_id == Document.id)
        .order_by(ReviewResult.reviewed_at.desc())
    )
    result = await db.execute(query)
    history = []
    
    for row in result:
        review = row[0]
        filename = row[1]
        
        # Determine status
        score = review.compliance_score
        if score >= 90: status = "COMPLIANT"
        elif score >= 70: status = "MOSTLY COMPLIANT"
        elif score >= 50: status = "NEEDS REVIEW"
        else: status = "NON-COMPLIANT"
        
        history.append(HistoryItem(
            review_id=review.id,
            document_id=review.document_id,
            filename=filename,
            compliance_score=score,
            reviewed_at=review.reviewed_at,
            status=status
        ))
        
    return history

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all uploaded documents."""
    result = await db.execute(select(Document).order_by(Document.uploaded_at.desc()))
    return result.scalars().all()


# ============ NDA Cleanup Endpoints ============

@router.get("/cleanup/{document_id}", response_model=CleanupResultResponse)
async def get_cleanup_result(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the NDA cleanup result for a document."""
    result = await db.execute(
        select(CleanupResult)
        .where(CleanupResult.document_id == document_id)
        .order_by(CleanupResult.created_at.desc())
        .limit(1)
    )
    db_cleanup = result.scalar_one_or_none()
    
    if not db_cleanup:
        raise HTTPException(status_code=404, detail="No cleanup result found for this document")
    
    return db_cleanup


@router.post("/cleanup/{document_id}/rerun", response_model=CleanupResultResponse)
async def rerun_cleanup(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Re-run NDA cleanup analysis for a document."""
    # Get document
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    db_doc = doc_result.scalar_one_or_none()
    
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Perform cleanup
    try:
        cleanup_result = await cleanup_service.perform_cleanup(db_doc.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NDA cleanup failed: {str(e)}")
    
    # Store new cleanup result
    db_cleanup = CleanupResult(
        document_id=document_id,
        original_content=db_doc.content,
        cleaned_indonesian=cleanup_result.get("cleaned_indonesian", ""),
        cleaned_english=cleanup_result.get("cleaned_english", ""),
        change_summary=cleanup_result.get("change_summary", []),
        open_items=cleanup_result.get("open_items", []),
        issues=cleanup_result.get("issues", [])
    )
    db.add(db_cleanup)
    await db.flush()
    
    return db_cleanup


@router.get("/cleanup/{document_id}/issues")
async def get_cleanup_issues(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get only the issues from the cleanup result."""
    result = await db.execute(
        select(CleanupResult)
        .where(CleanupResult.document_id == document_id)
        .order_by(CleanupResult.created_at.desc())
        .limit(1)
    )
    db_cleanup = result.scalar_one_or_none()
    
    if not db_cleanup:
        raise HTTPException(status_code=404, detail="No cleanup result found for this document")
    
    return {
        "document_id": document_id,
        "issues": db_cleanup.issues or [],
        "open_items": db_cleanup.open_items or [],
        "change_summary": db_cleanup.change_summary or []
    }
