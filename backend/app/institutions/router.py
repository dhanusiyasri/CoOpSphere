from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.institutions.models import Institution
from app.users.models import User

router = APIRouter(prefix="/institutions", tags=["Institutions"])


class InstitutionCreate(BaseModel):
    name: str
    institution_type: str
    state: str | None = None
    district: str | None = None


class InstitutionResponse(InstitutionCreate):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}


@router.get("", response_model=list[InstitutionResponse])
def list_institutions(db: Session = Depends(get_db), _user: User = Depends(require_roles("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER", "TRAINEE", "EMPLOYER"))):
    return db.scalars(select(Institution).order_by(Institution.name)).all()


@router.post("", response_model=InstitutionResponse)
def create_institution(payload: InstitutionCreate, db: Session = Depends(get_db), _admin: User = Depends(require_roles("NCCT_ADMIN"))):
    institution = Institution(**payload.model_dump())
    db.add(institution)
    db.commit()
    db.refresh(institution)
    return institution
