from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.student import StudentRead


class ExamStudentCreate(BaseModel):
    exam_planning_id: int
    student_id: int
    phase: Optional[str] = Field(default=None, max_length=100)
    result: Optional[str] = Field(default=None, max_length=50)


class ExamStudentUpdate(BaseModel):
    phase: Optional[str] = Field(default=None, max_length=100)
    result: Optional[str] = Field(default=None, max_length=50)


class ExamStudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_planning_id: int
    student_id: int
    phase: Optional[str]  # nullable — fallback naar student.phase in de business-laag
    result: Optional[str]
    student: StudentRead
    created_at: datetime
    updated_at: datetime