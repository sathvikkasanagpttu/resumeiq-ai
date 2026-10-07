import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, JSON
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class VectorType(TypeDecorator):
    """
    SQLAlchemy type decorator for vector embeddings:
    - PostgreSQL (production): maps to native pgvector Vector(dim) with cosine index support.
    - SQLite (dev/test only): falls back to JSON array serialization.
      NOTE: The SQLite storage path is strictly for local development and unit testing.
      Production deployments MUST use PostgreSQL with the pgvector extension.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 768, *args, **kwargs):
        self.dim = dim
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    # category: skill_definition, role_taxonomy, resume_principle, industry_terminology, learning_resource
    category = Column(String(100), nullable=False, index=True)
    content = Column(Text, nullable=False)
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, default=0)
    content = Column(Text, nullable=False)
    embedding = Column(VectorType(768), nullable=True)  # pgvector Vector(768) in PG; JSON in SQLite dev
    metadata_info = Column(JSON, default=dict)

    document = relationship("KnowledgeDocument", back_populates="chunks")

