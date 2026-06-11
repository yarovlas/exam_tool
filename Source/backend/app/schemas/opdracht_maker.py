from datetime import date, time
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.assignment import AssignmentProductRead, AssignmentRead
from app.schemas.product import ProductRead


ProductRole = Literal["required", "choice", "surprise"]


class OpdrachtMakerStudentRead(BaseModel):
    id: int
    student_id: int
    student_number: str
    name: str
    program_code: str
    phase: str
    email: Optional[str]
    placement_group: Optional[str]


class OpdrachtMakerExamRead(BaseModel):
    id: int
    exam_date: date
    exam_type: str
    room: str
    exam_time: time
    status: str


class OpdrachtMakerNormRead(BaseModel):
    min_regular_stars: int
    min_total_stars: int


class OpdrachtMakerProductGroupRead(BaseModel):
    role: ProductRole
    order: int
    label: str
    category: Optional[str]
    products: list[ProductRead]


class OpdrachtMakerContextRead(BaseModel):
    exam_student_id: int
    student: OpdrachtMakerStudentRead
    exam: OpdrachtMakerExamRead
    norm: OpdrachtMakerNormRead
    required_groups: list[OpdrachtMakerProductGroupRead]
    choice_groups: list[OpdrachtMakerProductGroupRead]
    used_product_ids: list[int]


class OpdrachtMakerSelection(BaseModel):
    product_id: int
    product_role: ProductRole
    product_order: int = Field(gt=0)


class OpdrachtMakerCalculateRequest(BaseModel):
    exam_student_id: int
    products: list[OpdrachtMakerSelection] = Field(min_length=1)


class OpdrachtMakerCalculateRead(BaseModel):
    regular_stars: int
    required_stars: int
    total_stars: int
    min_regular_stars: int
    min_total_stars: int
    regular_valid: bool
    total_valid: bool
    duplicate_product_ids: list[int]
    surprise_suggestions: list[ProductRead]


class OpdrachtMakerCreateRequest(OpdrachtMakerCalculateRequest):
    status: Literal["draft", "confirmed"] = "draft"
    allow_reuse: bool = False
    replace_existing: bool = False


class OpdrachtMakerCreateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assignment: AssignmentRead
    assignment_products: list[AssignmentProductRead]
    calculation: OpdrachtMakerCalculateRead
