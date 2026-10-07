#!/usr/bin/env python3
"""
Explicit opt-in script to seed a demo account for local development/testing.
Never runs automatically, and refuses to run in production.
Usage:
    python scripts/seed_demo.py
"""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, CandidateProfile
from app.services.rag.retriever import rag_retriever

def seed_demo_user():
    if settings.ENVIRONMENT.lower() in ("production", "prod"):
        print("ERROR: Refusing to seed demo data in a production environment.")
        sys.exit(1)

    with SessionLocal() as db:
        rag_retriever.sync_to_db(db)
        existing = db.query(User).filter(User.email == "demo@resumeiq.ai").first()
        if existing:
            print("Demo user 'demo@resumeiq.ai' already exists.")
            return

        demo_user = User(
            email="demo@resumeiq.ai",
            hashed_password=get_password_hash("ResumeIQ2026!"),
            full_name="Sarah Chen",
            role="candidate"
        )
        db.add(demo_user)
        db.flush()

        profile = CandidateProfile(
            user_id=demo_user.id,
            headline="Senior Backend & AI Systems Engineer",
            summary="Over 6 years of experience building high-throughput distributed systems and LLM/RAG pipelines.",
            total_experience_years=6.0,
            seniority_level="Senior",
            location="San Francisco, CA"
        )
        db.add(profile)
        db.commit()
        print("Successfully seeded demo user 'demo@resumeiq.ai' (Password: ResumeIQ2026!).")

if __name__ == "__main__":
    seed_demo_user()
