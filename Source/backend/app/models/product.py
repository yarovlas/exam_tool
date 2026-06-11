from datetime import datetime
from typing import Literal, Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.exam_planning import Base

ProductType = Literal["regular", "surprise"]


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    speciality_code: Mapped[str] = mapped_column(String(50), nullable=False)
    speciality_name: Mapped[Optional[str]] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    stars: Mapped[Optional[int]] = mapped_column(Integer)
    document_link: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    assignment_products: Mapped[list["AssignmentProduct"]] = relationship(
        "AssignmentProduct", back_populates="product"
    )
