from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)) -> Student:
    student = Student(
        student_number=payload.student_number,
        name=payload.name,
        program_code=payload.program_code,
        phase=payload.phase,
        email=payload.email,
        placement_group=payload.placement_group,
    )

    db.add(student)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student number already exists",
        ) from exc

    db.refresh(student)
    return student


@router.get("", response_model=list[StudentRead])
def list_students(
    program_code: Optional[str] = Query(default=None),
    phase: Optional[str] = Query(default=None),
    placement_group: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Student]:
    query = select(Student)

    if program_code:
        query = query.where(Student.program_code == program_code)

    if phase:
        query = query.where(Student.phase == phase)

    if placement_group:
        query = query.where(Student.placement_group == placement_group)

    query = query.order_by(Student.name.asc()).limit(limit).offset(offset)
    students = db.execute(query).scalars().all()
    return list(students)


@router.get("/{student_id}", response_model=StudentRead)
def get_student(student_id: int, db: Session = Depends(get_db)) -> Student:
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    return student


@router.patch("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
) -> Student:
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(student, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student number already exists",
        ) from exc

    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)) -> None:
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    db.delete(student)
    db.commit()
