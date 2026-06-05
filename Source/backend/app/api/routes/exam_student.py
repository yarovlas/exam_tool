from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.exam_student import ExamStudent
from app.schemas.exam_student import ExamStudentCreate, ExamStudentRead, ExamStudentUpdate

router = APIRouter(prefix="/exam-students", tags=["exam-students"])


@router.post("", response_model=ExamStudentRead, status_code=status.HTTP_201_CREATED)
def create_exam_student(payload: ExamStudentCreate, db: Session = Depends(get_db)) -> ExamStudent:
    exam_student = ExamStudent(
        exam_planning_id=payload.exam_planning_id,
        student_id=payload.student_id,
        phase=payload.phase,
        result=payload.result,
    )

    db.add(exam_student)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already linked to this exam",
        ) from exc

    db.refresh(exam_student)
    return exam_student


@router.get("", response_model=list[ExamStudentRead])
def list_exam_students(
    exam_planning_id: Optional[int] = Query(default=None),
    student_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ExamStudent]:
    query = select(ExamStudent)

    if exam_planning_id is not None:
        query = query.where(ExamStudent.exam_planning_id == exam_planning_id)

    if student_id is not None:
        query = query.where(ExamStudent.student_id == student_id)

    query = query.order_by(ExamStudent.id.asc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    return list(items)


@router.get("/{exam_student_id}", response_model=ExamStudentRead)
def get_exam_student(exam_student_id: int, db: Session = Depends(get_db)) -> ExamStudent:
    exam_student = db.get(ExamStudent, exam_student_id)

    if exam_student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam-student link not found")

    return exam_student


@router.patch("/{exam_student_id}", response_model=ExamStudentRead)
def update_exam_student(
    exam_student_id: int,
    payload: ExamStudentUpdate,
    db: Session = Depends(get_db),
) -> ExamStudent:
    exam_student = db.get(ExamStudent, exam_student_id)

    if exam_student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam-student link not found")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(exam_student, field, value)

    db.commit()
    db.refresh(exam_student)
    return exam_student


@router.delete("/{exam_student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam_student(exam_student_id: int, db: Session = Depends(get_db)) -> None:
    exam_student = db.get(ExamStudent, exam_student_id)

    if exam_student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam-student link not found")

    db.delete(exam_student)
    db.commit()
