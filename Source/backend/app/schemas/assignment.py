from datetime import datetime
from typing import Optional

from app.models.assignment import AssignmentStatus

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    exam_student_id: int
    status: AssignmentStatus = "confirmed"
    regular_stars: int = Field(default=0, ge=0)
    required_stars: int = Field(default=0, ge=0)
    total_stars: int = Field(default=0, ge=0)
    result: Optional[str] = Field(default=None, max_length=50)


class AssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_student_id: int
    status: AssignmentStatus
    regular_stars: int
    required_stars: int
    total_stars: int
    result: Optional[str]
    created_at: datetime
    updated_at: datetime


class AssignmentUpdate(BaseModel):
    status: Optional[AssignmentStatus] = None
    regular_stars: Optional[int] = Field(default=None, ge=0)
    required_stars: Optional[int] = Field(default=None, ge=0)
    total_stars: Optional[int] = Field(default=None, ge=0)
    result: Optional[str] = Field(default=None, max_length=50)


class AssignmentProductCreate(BaseModel):
    assignment_id: int
    product_id: Optional[int] = None
    product_role: str = Field(min_length=1, max_length=50)
    product_order: int = Field(default=1, gt=0)
    product_text: Optional[str] = None
    stars: int = Field(default=0, ge=0)
    result: Optional[str] = Field(default=None, max_length=50)


class AssignmentProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    product_id: Optional[int]
    product_role: str
    product_order: int
    product_text: Optional[str]
    stars: int
    result: Optional[str]
    created_at: datetime
    updated_at: datetime


class AssignmentProductUpdate(BaseModel):
    product_id: Optional[int] = None
    product_role: Optional[str] = Field(default=None, min_length=1, max_length=50)
    product_order: Optional[int] = Field(default=None, gt=0)
    product_text: Optional[str] = None
    stars: Optional[int] = Field(default=None, ge=0)
    result: Optional[str] = Field(default=None, max_length=50)
