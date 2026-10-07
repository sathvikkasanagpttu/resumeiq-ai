import os
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, String, Integer, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from alembic.config import Config
from alembic import command
from app.core.database import Base
from app.models.rag import VectorType, KnowledgeChunk

backend_dir = Path(__file__).resolve().parent.parent.parent

def test_alembic_upgrade_from_scratch_and_check():
    """
    Test that an empty database can be upgraded to head with Alembic,
    and that `alembic check` confirms zero schema drift against current SQLAlchemy models.
    """
    temp_db = tempfile.mktemp(suffix=".db")
    db_url = f"sqlite:///{temp_db}"

    try:
        cfg = Config(str(backend_dir / "alembic.ini"))
        cfg.set_main_option("script_location", str(backend_dir / "migrations"))
        cfg.set_main_option("sqlalchemy.url", db_url)

        # 1. Upgrade from scratch
        command.upgrade(cfg, "head")

        # 2. Assert zero schema drift
        command.check(cfg)
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)

def test_all_foreign_keys_have_ondelete_rules():
    """
    Ensure all foreign keys across all defined SQLAlchemy models have explicit ondelete rules
    (CASCADE or SET NULL) to prevent orphaned records or silent constraint errors.
    """
    for table_name, table in Base.metadata.tables.items():
        for fk in table.foreign_keys:
            assert fk.ondelete is not None, f"Foreign key {fk} on table {table_name} lacks an ondelete rule!"
            assert fk.ondelete.upper() in ("CASCADE", "SET NULL", "RESTRICT"), (
                f"Foreign key {fk} on table {table_name} has invalid ondelete rule: {fk.ondelete}"
            )

def test_critical_foreign_keys_are_indexed():
    """
    Ensure critical foreign keys (e.g. user_id, resume_id, job_id, version_id) have explicit indexes.
    """
    for table_name, table in Base.metadata.tables.items():
        indexed_cols = set()
        for idx in table.indexes:
            for col in idx.columns:
                indexed_cols.add(col.name)
        
        for col in table.columns:
            if col.index or col.primary_key or col.unique:
                indexed_cols.add(col.name)
                
            if col.name in ("user_id", "resume_id", "job_id", "version_id", "document_id"):
                assert col.name in indexed_cols, (
                    f"Column '{col.name}' on table '{table_name}' should be indexed for query performance!"
                )

def test_vectortype_dialect_behavior():
    """
    Ensure VectorType resolves to pgvector Vector on PostgreSQL,
    and falls back to JSON on SQLite (documented as dev/test only).
    """
    from sqlalchemy.dialects import postgresql, sqlite

    vec_type = VectorType(dim=768)
    
    # SQLite dialect check (local dev & testing)
    sqlite_impl = vec_type.load_dialect_impl(sqlite.dialect())
    assert isinstance(sqlite_impl, JSON)

    # PostgreSQL dialect check (production pgvector)
    pg_impl = vec_type.load_dialect_impl(postgresql.dialect())
    assert pg_impl.__class__.__name__.upper() == "VECTOR"
    assert pg_impl.dim == 768

