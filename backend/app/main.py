from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.core.config import settings
from app.institutions.router import router as institutions_router
from app.users.router import router as users_router
from app.training.router import router as training_router
from app.training.schedule_router import router as training_schedule_router
from app.training.logistics_router import router as training_logistics_router
from app.training.evaluation_router import router as training_evaluation_router
from app.attendance.router import router as attendance_router
from app.lms.router import router as lms_router
from app.credentials.router import router as credentials_router
from app.careers.router import router as careers_router
from app.careers.profile_router import router as career_profile_router
from app.intelligence.router import router as intelligence_router
from app.dashboard.router import router as dashboard_router
from app.skills.router import router as skills_router
from app.skills.passport_router import router as skill_passport_router
from app.skills.recommendation_router import router as skill_recommendation_router
from app.notifications import router as notifications_router

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
def root():
    return {"name": settings.app_name, "status": "running", "version": "0.1.0"}


@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy"}


app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(institutions_router, prefix=settings.api_v1_prefix)
app.include_router(training_router, prefix=settings.api_v1_prefix)
app.include_router(training_schedule_router, prefix=settings.api_v1_prefix)
app.include_router(training_logistics_router, prefix=settings.api_v1_prefix)
app.include_router(training_evaluation_router, prefix=settings.api_v1_prefix)
app.include_router(attendance_router, prefix=settings.api_v1_prefix)
app.include_router(lms_router, prefix=settings.api_v1_prefix)
app.include_router(credentials_router, prefix=settings.api_v1_prefix)
app.include_router(careers_router, prefix=settings.api_v1_prefix)
app.include_router(career_profile_router, prefix=settings.api_v1_prefix)
app.include_router(intelligence_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(skills_router, prefix=settings.api_v1_prefix)
app.include_router(skill_passport_router, prefix=settings.api_v1_prefix)
app.include_router(skill_recommendation_router, prefix=settings.api_v1_prefix)
app.include_router(notifications_router, prefix=settings.api_v1_prefix)
