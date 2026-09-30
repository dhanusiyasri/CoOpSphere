from pydantic import BaseModel

class SkillGapItem(BaseModel):
    skill_id: int
    code: str
    name: str
    category: str
    current_proficiency: int
    target_proficiency: int
    gap: int

class LearningRecommendation(BaseModel):
    course_id: int
    course_code: str
    title: str
    category: str
    level: str
    delivery_mode: str
    match_score: int
    matched_skills: list[str]
    reason: str

class JobRecommendation(BaseModel):
    job_id: int
    title: str
    organization_name: str
    location: str
    employment_type: str
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    reason: str

class SkillRecommendations(BaseModel):
    trainee_id: int
    trainee_name: str
    digital_literacy_level: str
    skill_gaps: list[SkillGapItem]
    learning_recommendations: list[LearningRecommendation]
    job_recommendations: list[JobRecommendation]
