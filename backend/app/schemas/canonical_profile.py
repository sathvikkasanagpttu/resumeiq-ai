from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

SourceType = Literal["extracted", "user_confirmed", "ai_suggested_pending"]
EvidenceStrengthType = Literal["verified", "weak", "inferred", "missing", "uncertain"]
UsageDepthType = Literal["listed_only", "used_in_project", "used_in_production_with_outcome"]

class SourceSpan(BaseModel):
    page: Optional[int] = 1
    start_char: Optional[int] = 0
    end_char: Optional[int] = 0
    text_snippet: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)

class GroundedField(BaseModel):
    value: Any
    source: SourceType = "extracted"
    source_span: Optional[SourceSpan] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    user_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class GroundedBullet(BaseModel):
    id: Optional[str] = None
    value: str
    source: SourceType = "extracted"
    source_span: Optional[SourceSpan] = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    evidence_ids: List[str] = Field(default_factory=list)
    action_verb: Optional[str] = None
    quantified_metrics: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    is_accepted: bool = True  # If ai_suggested_pending, must be accepted by user to render

    model_config = ConfigDict(from_attributes=True)

class GroundedSkillItem(BaseModel):
    id: Optional[str] = None
    name: str
    normalized_name: str
    category: Optional[str] = "technical"
    source: SourceType = "extracted"
    source_span: Optional[SourceSpan] = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    evidence_strength: EvidenceStrengthType = "verified"
    usage_depth: UsageDepthType = "listed_only"
    evidence_quote: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class GroundedSocialProfile(BaseModel):
    network: str  # GitHub, LinkedIn, Portfolio, etc.
    username: Optional[str] = None
    url: str
    source: SourceType = "extracted"
    source_span: Optional[SourceSpan] = None
    confidence: float = 1.0

    model_config = ConfigDict(from_attributes=True)

class LocationInfo(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country_code: Optional[str] = None
    postal_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CanonicalBasics(BaseModel):
    name: GroundedField
    label: GroundedField  # e.g., "Senior Backend Engineer"
    email: GroundedField
    phone: GroundedField
    url: Optional[GroundedField] = None
    summary: GroundedField
    location: GroundedField
    profiles: List[GroundedSocialProfile] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class CanonicalExperience(BaseModel):
    id: Optional[str] = None
    company: GroundedField
    position: GroundedField
    url: Optional[GroundedField] = None
    start_date: GroundedField
    end_date: GroundedField
    is_current: GroundedField
    duration_months: int = 0
    location: Optional[GroundedField] = None
    summary: Optional[GroundedField] = None
    highlights: List[GroundedBullet] = Field(default_factory=list)
    technologies: List[GroundedSkillItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class CanonicalProject(BaseModel):
    id: Optional[str] = None
    name: GroundedField
    description: GroundedField
    highlights: List[GroundedBullet] = Field(default_factory=list)
    technologies: List[GroundedSkillItem] = Field(default_factory=list)
    url: Optional[GroundedField] = None

    model_config = ConfigDict(from_attributes=True)

class CanonicalEducation(BaseModel):
    id: Optional[str] = None
    institution: GroundedField
    area: GroundedField  # Field of Study
    study_type: GroundedField  # Degree / B.S.
    start_date: Optional[GroundedField] = None
    end_date: GroundedField  # Graduation date
    score: Optional[GroundedField] = None  # GPA / Honours

    model_config = ConfigDict(from_attributes=True)

class CanonicalCertification(BaseModel):
    id: Optional[str] = None
    name: GroundedField
    issuer: GroundedField
    date: GroundedField
    expiration_date: Optional[GroundedField] = None
    url: Optional[GroundedField] = None

    model_config = ConfigDict(from_attributes=True)

class CanonicalAchievement(BaseModel):
    id: Optional[str] = None
    title: GroundedField
    date: Optional[GroundedField] = None
    summary: GroundedField

    model_config = ConfigDict(from_attributes=True)

class CanonicalSkillCategory(BaseModel):
    category_name: str
    skills: List[GroundedSkillItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class CanonicalProfile(BaseModel):
    """
    JSON Resume compliant canonical candidate profile.
    Single Source of Truth for all generated resume variations.
    """
    schema_version: str = "2.0.0"
    basics: CanonicalBasics
    experience: List[CanonicalExperience] = Field(default_factory=list)
    projects: List[CanonicalProject] = Field(default_factory=list)
    education: List[CanonicalEducation] = Field(default_factory=list)
    skills: List[CanonicalSkillCategory] = Field(default_factory=list)
    certifications: List[CanonicalCertification] = Field(default_factory=list)
    achievements: List[CanonicalAchievement] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    def get_renderable_copy(self) -> "CanonicalProfile":
        """
        Returns a clean copy of the profile containing ONLY:
        - 'extracted' or 'user_confirmed' items
        - 'ai_suggested_pending' items that have been explicitly marked is_accepted == True.
        Strictly guarantees NO unconfirmed AI suggestions appear in exported resumes.
        """
        import copy
        data = self.model_dump()

        # Filter experience bullets
        for exp in data.get("experience", []):
            exp["highlights"] = [
                h for h in exp.get("highlights", [])
                if h.get("source") in ("extracted", "user_confirmed") or h.get("is_accepted", False)
            ]

        # Filter project highlights
        for proj in data.get("projects", []):
            proj["highlights"] = [
                h for h in proj.get("highlights", [])
                if h.get("source") in ("extracted", "user_confirmed") or h.get("is_accepted", False)
            ]

        # Filter skills
        for cat in data.get("skills", []):
            cat["skills"] = [
                s for s in cat.get("skills", [])
                if s.get("source") in ("extracted", "user_confirmed")
            ]

        return CanonicalProfile.model_validate(data)

    def get_redacted_copy(self) -> "CanonicalProfile":
        """
        Returns a privacy-hardened copy with PII redacted (name, email, phone, location masked).
        Useful for blind recruiting, public sharing, and benchmark evaluation.
        """
        copy_profile = self.get_renderable_copy()
        data = copy_profile.model_dump()

        b = data.get("basics", {})
        # Redact Name
        orig_name = str(b.get("name", {}).get("value", "") or "")
        initials = "".join([part[0].upper() for part in orig_name.split() if part]) or "X"
        b["name"]["value"] = f"Candidate {initials}"

        # Redact Email
        if b.get("email"):
            b["email"]["value"] = "candidate.redacted@domain-privacy.net"

        # Redact Phone
        if b.get("phone"):
            b["phone"]["value"] = "+1 (***) ***-****"

        # Generalize location
        if b.get("location") and isinstance(b["location"].get("value"), dict):
            b["location"]["value"]["address"] = None
            b["location"]["value"]["postal_code"] = None

        # Redact profile URLs
        for pr in b.get("profiles", []):
            pr["username"] = "redacted_user"
            pr["url"] = f"https://{pr.get('network', 'profile').lower()}.com/in/redacted"

        return CanonicalProfile.model_validate(data)
