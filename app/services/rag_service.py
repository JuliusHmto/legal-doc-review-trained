"""
Legal Document Review System - RAG Service
Handles vector embeddings and semantic search using PostgreSQL + pgvector.
"""
from typing import List, Optional
from uuid import UUID
from openai import AsyncOpenAI
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import Embedding

settings = get_settings()


class RAGService:
    """Service for RAG operations using pgvector."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.embedding_model = settings.embedding_model
        self.embedding_dimension = 1536
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding vector for text using OpenAI."""
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    async def store_embeddings(
        self, 
        db: AsyncSession, 
        module_id: UUID, 
        chunks: List[str]
    ) -> List[UUID]:
        """Store text chunks with their embeddings in the database."""
        embedding_ids = []
        
        for chunk in chunks:
            # Create embedding for chunk
            embedding_vector = await self.create_embedding(chunk)
            
            # Store in database
            embedding = Embedding(
                module_id=module_id,
                chunk_text=chunk,
                embedding=embedding_vector
            )
            db.add(embedding)
            embedding_ids.append(embedding.id)
        
        await db.commit()
        return embedding_ids
    
    async def search_similar(
        self, 
        db: AsyncSession, 
        query: str, 
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[dict]:
        """Search for similar chunks using cosine similarity."""
        # Create embedding for query
        query_embedding = await self.create_embedding(query)
        
        # Convert to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Query using pgvector cosine similarity
        sql = text(f"""
            SELECT 
                id,
                module_id,
                chunk_text,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM embeddings
            WHERE 1 - (embedding <=> :embedding::vector) > :threshold
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """)
        
        result = await db.execute(
            sql,
            {
                "embedding": embedding_str,
                "threshold": similarity_threshold,
                "limit": limit
            }
        )
        
        rows = result.fetchall()
        
        return [
            {
                "id": str(row.id),
                "module_id": str(row.module_id),
                "chunk_text": row.chunk_text,
                "similarity_score": float(row.similarity)
            }
            for row in rows
        ]
    
    async def search_by_module(
        self, 
        db: AsyncSession, 
        module_id: UUID, 
        query: str,
        limit: int = 3
    ) -> List[dict]:
        """Search for similar chunks within a specific module."""
        query_embedding = await self.create_embedding(query)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        sql = text(f"""
            SELECT 
                id,
                module_id,
                chunk_text,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM embeddings
            WHERE module_id = :module_id
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """)
        
        result = await db.execute(
            sql,
            {
                "embedding": embedding_str,
                "module_id": module_id,
                "limit": limit
            }
        )
        
        rows = result.fetchall()
        
        return [
            {
                "id": str(row.id),
                "module_id": str(row.module_id),
                "chunk_text": row.chunk_text,
                "similarity_score": float(row.similarity)
            }
            for row in rows
        ]
    
    async def get_all_module_chunks(
        self, 
        db: AsyncSession, 
        module_id: UUID
    ) -> List[str]:
        """Get all chunks for a specific module."""
        result = await db.execute(
            select(Embedding.chunk_text).where(Embedding.module_id == module_id)
        )
        return [row[0] for row in result.fetchall()]
    
    async def delete_module_embeddings(
        self, 
        db: AsyncSession, 
        module_id: UUID
    ) -> int:
        """Delete all embeddings for a module."""
        result = await db.execute(
            text("DELETE FROM embeddings WHERE module_id = :module_id"),
            {"module_id": module_id}
        )
        await db.commit()
        return result.rowcount
