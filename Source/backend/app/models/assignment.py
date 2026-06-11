from datetime import datetime
from typing import Literal, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.exam_planning import Base

AssignmentStatus = Literal["draft", "confirmed", "completed", "cancelled"]


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        UniqueConstraint("exam_student_id", name="assignments_exam_student_unique"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_student_id: Mapped[int] = mapped_column(ForeignKey("exam_students.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    regular_stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    required_stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    exam_student: Mapped["ExamStudent"] = relationship("ExamStudent", back_populates="assignment")
    assignment_products: Mapped[list["AssignmentProduct"]] = relationship(
        "AssignmentProduct", back_populates="assignment", cascade="all, delete-orphan"
    )
