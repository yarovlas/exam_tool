from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, String, Time, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ExamPlanning(Base):
    __tablename__ = "exam_planning"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    exam_type: Mapped[str] = mapped_column(String(100), nullable=False)
    room: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="planned")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    exam_assessors: Mapped[list["ExamAssessor"]] = relationship(
        "ExamAssessor", back_populates="exam_planning", cascade="all, delete-orphan"
    )
