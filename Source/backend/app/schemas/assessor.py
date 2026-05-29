from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


AssessorType = Literal["external", "teacher"]


class AssessorCreate(BaseModel):
    assessor_type: AssessorType
    name: str = Field(min_length=1, max_length=255)
    organization: Optional[str] = Field(default=None, max_length=255)
    salutation: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    postal_city: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    recruitment_status: Optional[str] = Field(default=None, max_length=100)


class AssessorUpdate(BaseModel):
    assessor_type: Optional[AssessorType] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    organization: Optional[str] = Field(default=None, max_length=255)
    salutation: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    postal_city: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    recruitment_status: Optional[str] = Field(default=None, max_length=100)


class AssessorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessor_type: AssessorType
    name: str
    organization: Optional[str]
    salutation: Optional[str]
    address: Optional[str]
    postal_city: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    recruitment_status: Optional[str]
    created_at: datetime
    updated_at: datetime


class ExamAssessorCreate(BaseModel):
    assessor_id: int
    assessor_order: int = Field(ge=1, le=2)


class ExamAssessorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessor_id: int
    assessor_order: int
    assessor: AssessorRead
    created_at: datetime
    updated_at: datetime
