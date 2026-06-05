from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, String, func, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.exam_planning import Base


class Assessor(Base):
    __tablename__ = "assessors"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessor_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[Optional[str]] = mapped_column(String(255))
    salutation: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(String(500))
    postal_city: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    recruitment_status: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    exam_assessors: Mapped[list["ExamAssessor"]] = relationship(
        "ExamAssessor", back_populates="assessor"
    )


class ExamAssessor(Base):
    __tablename__ = "exam_assessors"
    __table_args__ = (
        UniqueConstraint("exam_planning_id", "assessor_order", name="exam_assessors_unique_slot"),
        UniqueConstraint("exam_planning_id", "assessor_id", name="exam_assessors_unique_assessor"),
        CheckConstraint("assessor_order IN (1, 2)", name="exam_assessors_order_check"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_planning_id: Mapped[int] = mapped_column(ForeignKey("exam_planning.id", ondelete="CASCADE"))
    assessor_id: Mapped[int] = mapped_column(ForeignKey("assessors.id", ondelete="RESTRICT"))
    assessor_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    assessor: Mapped[Assessor] = relationship("Assessor", back_populates="exam_assessors")
    exam_planning: Mapped["ExamPlanning"] = relationship("ExamPlanning", back_populates="exam_assessors")
