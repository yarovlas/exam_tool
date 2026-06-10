from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.exam_planning import Base


class ExamStudent(Base):
    __tablename__ = "exam_students"
    __table_args__ = (
        UniqueConstraint("exam_planning_id", "student_id", name="exam_students_exam_student_unique"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_planning_id: Mapped[int] = mapped_column(ForeignKey("exam_planning.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    phase: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    exam_planning = relationship("ExamPlanning", back_populates="exam_students")
    student: Mapped["Student"] = relationship("Student", back_populates="exam_students")
    assignment: Mapped[Optional["Assignment"]] = relationship(
        "Assignment", back_populates="exam_student", cascade="all, delete-orphan", uselist=False
    )
