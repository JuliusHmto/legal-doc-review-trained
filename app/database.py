"""
Legal Document Review System - Database Connection and Models
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid

from app.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Document(Base):
    """Uploaded documents table."""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    content = Column(Text)
    uploaded_at = Column(DateTime, server_default=func.now())


class TrainingModule(Base):
    """Generated training modules table."""
    __tablename__ = "training_modules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    module_content = Column(JSONB)  # Structured training module
    summary = Column(Text)  # Brief summary of the module
    created_at = Column(DateTime, server_default=func.now())


class Embedding(Base):
    """Vector embeddings for RAG."""
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("training_modules.id"), nullable=False)
    chunk_text = Column(Text)
    embedding = Column(Vector(1536))  # OpenAI embedding dimension
    created_at = Column(DateTime, server_default=func.now())


class ReviewResult(Base):
    """Compliance review results."""
    __tablename__ = "review_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    compliance_score = Column(Integer)  # 0-100
    issues = Column(JSONB)  # List of compliance issues
    recommendations = Column(JSONB)  # Suggested fixes
    law_references = Column(JSONB)  # Relevant Indonesian laws cited
    reviewed_at = Column(DateTime, server_default=func.now())


async def init_db():
    """Initialize database tables and pgvector extension."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Import text for raw SQL
from sqlalchemy import text
