import os
import sys
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from alembic.config import Config
from alembic import command

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import Base, get_db
import app.core.database as db_module
from app.core.rate_limit import rate_limiter
from app.main import app

@pytest.fixture(autouse=True)
def reset_rate_limits_fixture():
    rate_limiter.reset()
    yield
    rate_limiter.reset()

@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db_session") / "test_resumeiq.db"
    return str(db_file)

@pytest.fixture(scope="session")
def test_engine(test_db_path):
    db_url = f"sqlite:///{test_db_path}"
    settings.DATABASE_URL = db_url
    
    # Run alembic migrations on this database
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    # Run migrations to head
    command.upgrade(alembic_cfg, "head")
    
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
    db_module.engine = engine
    db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def db_session(TestingSessionLocal):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def client(TestingSessionLocal):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
