from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class WizardQuestion(BaseModel):
    id: str
    category: str  # summary, metric, link, skill, timeline_gap, project_detail
    target_entity_id: Optional[str] = None
    target_section: str
    prompt_text: str
    context_hint: str
    example_answers: List[str] = Field(default_factory=list)
    has_metric_requested: bool = False

    model_config = ConfigDict(from_attributes=True)

class WizardAnswer(BaseModel):
    question_id: str
    answer_text: str
    confirmed_metric: Optional[str] = None
    confirmed_technologies: List[str] = Field(default_factory=list)

class WizardSessionResponse(BaseModel):
    resume_id: str
    total_questions: int
    questions: List[WizardQuestion]
    summary_message: str

    model_config = ConfigDict(from_attributes=True)

class WizardSubmitRequest(BaseModel):
    resume_id: str
    answers: List[WizardAnswer]

class WizardSubmitResponse(BaseModel):
    resume_id: str
    facts_added_count: int
    message: str
    next_step: str = "Proceed to Auto Resume Generation"
