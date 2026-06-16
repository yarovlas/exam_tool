from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class StudentCreate(BaseModel):
    student_number: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    program_code: str = Field(min_length=1, max_length=50)
    phase: str = Field(min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    placement_group: Optional[str] = Field(default=None, max_length=100)
    
class StudentUpdate(BaseModel):
    student_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    program_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    phase: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    placement_group: Optional[str] = Field(default=None, max_length=100)

class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_number: str
    name: str
    program_code: str
    phase: str
    email: Optional[str]
    placement_group: Optional[str]
    created_at: datetime
    updated_at: datetime
    
class StudentDelete(BaseModel):
    id: int