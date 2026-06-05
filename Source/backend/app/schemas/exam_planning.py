from datetime import date, datetime, time
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.assessor import ExamAssessorRead, ExamAssessorCreate
from app.schemas.exam_student import ExamStudentCreate, ExamStudentRead


PlanningStatus = Literal["planned", "confirmed", "completed", "cancelled"]
ExamType = Literal["practical", "avo", "keuzedeel", "profialdeel"]


class ExamPlanningCreate(BaseModel):
    exam_date: date
    exam_type: ExamType
    room: str = Field(min_length=1, max_length=100)
    exam_time: time
    status: PlanningStatus = "planned"
    assessors: Optional[list[ExamAssessorCreate]] = Field(default=None)
    students: Optional[list[ExamStudentCreate]] = Field(default=None)


class ExamPlanningUpdate(BaseModel):
    exam_date: Optional[date] = None
    exam_type: Optional[ExamType] = None
    room: Optional[str] = Field(default=None, min_length=1, max_length=100)
    exam_time: Optional[time] = None
    status: Optional[PlanningStatus] = None
    assessors: Optional[list[ExamAssessorCreate]] = None
    students: Optional[list[ExamStudentCreate]] = None


class ExamPlanningRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_date: date
    exam_type: str
    room: str
    exam_time: time
    status: PlanningStatus
    created_at: datetime
    updated_at: datetime
    exam_assessors: list[ExamAssessorRead] = []
    exam_students: list[ExamStudentRead] = []


class ExamplanningDelete(BaseModel):
    id: int

