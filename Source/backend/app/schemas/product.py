from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import ProductType


class ProductCreate(BaseModel):
    product_kind: ProductType
    speciality_code: str = Field(min_length=1, max_length=50)
    speciality_name: Optional[str] = Field(default=None, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    stars: int = Field(default=0, ge=0)
    document_link: Optional[str] = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_kind: ProductType
    speciality_code: str
    speciality_name: Optional[str]
    name: str
    category: Optional[str]
    stars: int
    document_link: Optional[str]
    created_at: datetime
    updated_at: datetime


class ProductUpdate(BaseModel):
    product_kind: Optional[ProductType] = None
    speciality_code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    speciality_name: Optional[str] = Field(default=None, max_length=255)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    stars: Optional[int] = Field(default=None, ge=0)
    document_link: Optional[str] = None
