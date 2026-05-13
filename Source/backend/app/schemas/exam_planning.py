from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PlanningStatus = Literal["planned", "confirmed", "completed", "cancelled"]
ExamType = Literal["practical", "avo", "keuzedeel", "profialdeel"]


class ExamPlanningCreate(BaseModel):
    exam_date: date
    exam_type: ExamType
    room: str = Field(min_length=1, max_length=100)
    exam_time: time
    status: PlanningStatus = "planned"


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
