import re

from pydantic import BaseModel, field_validator


_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+$")


class LoginRequest(BaseModel):
    # NCCT's local demo accounts intentionally use the .local domain.
    # Pydantic EmailStr rejects special-use domains such as .local, so the
    # application performs lightweight syntax validation instead.
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Enter a valid email address")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    institution_id: int | None

    model_config = {"from_attributes": True}
