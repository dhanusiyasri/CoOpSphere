from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.institutions.models import Institution
from app.users.models import User
from app.auth.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

ROLES = ("NCCT_ADMIN", "INSTITUTE_ADMIN", "TRAINER", "TRAINEE", "EMPLOYER")

class UserAdminResponse(UserResponse):
    is_active: bool
    institution_name: str | None = None

class UserUpdate(BaseModel):
    role: str | None = Field(default=None)
    institution_id: int | None = Field(default=None)
    is_active: bool | None = Field(default=None)

@router.get("", response_model=list[UserAdminResponse])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("NCCT_ADMIN")),
):
    rows = db.execute(
        select(User, Institution.name)
        .outerjoin(Institution, Institution.id == User.institution_id)
        .order_by(User.id)
    ).all()
    return [
        UserAdminResponse(
            id=user.id, full_name=user.full_name, email=user.email, role=user.role,
            institution_id=user.institution_id, is_active=user.is_active,
            institution_name=institution_name,
        )
        for user, institution_name in rows
    ]

@router.patch("/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("NCCT_ADMIN")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.role is not None:
        if payload.role not in ROLES:
            raise HTTPException(status_code=400, detail="Unsupported role")
        user.role = payload.role

    # Allow an explicit null to remove an institution assignment.
    if "institution_id" in payload.model_fields_set:
        if payload.institution_id is None:
            user.institution_id = None
        else:
            institution = db.get(Institution, payload.institution_id)
            if not institution:
                raise HTTPException(status_code=400, detail="Institution not found")
            if not institution.is_active:
                raise HTTPException(status_code=400, detail="Institution is inactive")
            user.institution_id = payload.institution_id

    if payload.is_active is not None:
        if user.id == admin.id and payload.is_active is False:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    institution_name = db.scalar(select(Institution.name).where(Institution.id == user.institution_id))
    return UserAdminResponse(
        id=user.id, full_name=user.full_name, email=user.email, role=user.role,
        institution_id=user.institution_id, is_active=user.is_active,
        institution_name=institution_name,
    )
