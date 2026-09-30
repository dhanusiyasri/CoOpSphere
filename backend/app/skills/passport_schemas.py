from datetime import datetime
from pydantic import BaseModel, Field

class SkillCatalogResponse(BaseModel):
    id: int; code: str; name: str; category: str; description: str | None; active: bool

class SkillAssignmentCreate(BaseModel):
    trainee_id: int
    skill_id: int
    proficiency: int = Field(ge=1, le=5)
    evidence_type: str = Field(default="TRAINER_VERIFIED", max_length=50)
    evidence_note: str | None = Field(default=None, max_length=1000)

class SkillItem(BaseModel):
    id: int
    skill_id: int
    code: str
    name: str
    category: str
    proficiency: int
    proficiency_label: str
    evidence_type: str
    evidence_note: str | None
    updated_at: datetime

class SkillGap(BaseModel):
    skill_id: int; code: str; name: str; category: str; current_proficiency: int; target_proficiency: int; gap: int

class SkillPassport(BaseModel):
    trainee_id: int
    trainee_name: str
    trainee_email: str
    digital_literacy_level: str
    skills: list[SkillItem]
    skill_gaps: list[SkillGap]
    total_skills: int
    verified_skills: int
