import pytest
from app.services.parser.document_reader import DocumentReader
from app.services.parser.section_detector import SectionDetector
from app.services.parser.entity_extractor import EntityExtractor
from app.core.exceptions import DocumentParsingError

def test_document_reader_validation():
    # Empty file
    with pytest.raises(DocumentParsingError):
        DocumentReader.validate_file("empty.txt", b"")

    # Unsupported format
    with pytest.raises(DocumentParsingError):
        DocumentReader.validate_file("archive.zip", b"dummy content")

    # Valid txt
    ext = DocumentReader.validate_file("resume.txt", b"Valid resume text")
    assert ext == "txt"

def test_section_detector():
    sample_resume = """
John Doe
john@example.com

PROFESSIONAL SUMMARY
Experienced backend engineer with 5 years experience.

WORK EXPERIENCE
Senior Engineer - Tech Corp
• Built distributed systems using Python and FastAPI.

EDUCATION
B.S. in Computer Science - State University (2020)

TECHNICAL SKILLS
Python, PostgreSQL, Docker
"""
    sections = SectionDetector.detect_sections(sample_resume)
    sec_types = [s.section_type for s in sections]
    assert "summary" in sec_types
    assert "experience" in sec_types
    assert "education" in sec_types
    assert "skills" in sec_types

def test_evidence_strength_discrimination():
    sections = {
        "experience": "Architected high-throughput services with Python and PostgreSQL, reducing latency by 40%.",
        "skills": "Python, Java, C++"
    }
    full_text = sections["experience"] + "\n" + sections["skills"]

    skills, evidence_items = EntityExtractor.extract_skills_with_evidence(sections, full_text)
    
    # Python in experience with action verb "Architected" and metric "40%" must be 'verified'
    python_skill = next((s for s in skills if s.normalized_skill == "Python"), None)
    assert python_skill is not None
    assert python_skill.evidence_strength == "verified"
    assert python_skill.confidence >= 0.90
