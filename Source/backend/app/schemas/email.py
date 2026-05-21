from pydantic import BaseModel, Field, field_validator


class TestEmailRequest(BaseModel):
    to_email: str = Field(..., min_length=3, max_length=255)
    recipient_name: str = Field(default="Exam Tool gebruiker", min_length=1, max_length=120)
    subject: str = Field(default="Mailtrap test vanuit Exam Tool", min_length=1, max_length=180)

    @field_validator("to_email")
    @classmethod
    def validate_to_email(cls, value: str) -> str:
        normalized = value.strip()
        if "@" not in normalized or "." not in normalized.rsplit("@", maxsplit=1)[-1]:
            raise ValueError("to_email must be a valid email address")
        return normalized


class TestEmailResponse(BaseModel):
    sent: bool
    message: str
    to_email: str
