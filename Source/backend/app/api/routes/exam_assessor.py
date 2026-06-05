from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.assessor import ExamAssessor
from app.schemas.assessor import ExamAssessorCreate, ExamAssessorRead

router = APIRouter(prefix="/exam-assessors", tags=["exam-assessors"])


@router.post("", response_model=ExamAssessorRead, status_code=status.HTTP_201_CREATED)
def create_exam_assessor(payload: ExamAssessorCreate, db: Session = Depends(get_db)) -> ExamAssessor:
    if payload.exam_planning_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="exam_planning_id is required",
        )

    exam_assessor = ExamAssessor(
        exam_planning_id=payload.exam_planning_id,
        assessor_id=payload.assessor_id,
        assessor_order=payload.assessor_order,
    )

    db.add(exam_assessor)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessor is already linked to this exam slot",
        ) from exc

    db.refresh(exam_assessor)
    return exam_assessor


@router.get("", response_model=list[ExamAssessorRead])
def list_exam_assessors(
    exam_planning_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ExamAssessor]:
    query = select(ExamAssessor)

    if exam_planning_id is not None:
        query = query.where(ExamAssessor.exam_planning_id == exam_planning_id)

    query = query.order_by(ExamAssessor.assessor_order.asc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    return list(items)


@router.get("/{exam_assessor_id}", response_model=ExamAssessorRead)
def get_exam_assessor(exam_assessor_id: int, db: Session = Depends(get_db)) -> ExamAssessor:
    exam_assessor = db.get(ExamAssessor, exam_assessor_id)

    if exam_assessor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam-assessor link not found")

    return exam_assessor


@router.delete("/{exam_assessor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam_assessor(exam_assessor_id: int, db: Session = Depends(get_db)) -> None:
    exam_assessor = db.get(ExamAssessor, exam_assessor_id)

    if exam_assessor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam-assessor link not found")

    db.delete(exam_assessor)
    db.commit()
