from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.exam_planning import Base


class AssignmentProduct(Base):
    __tablename__ = "assignment_products"
    __table_args__ = (
        UniqueConstraint("assignment_id", "product_role", "product_order", name="assignment_products_unique_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"))
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    product_role: Mapped[str] = mapped_column(String(50), nullable=False)
    product_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    product_text: Mapped[Optional[str]] = mapped_column(Text)
    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="assignment_products")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="assignment_products")
