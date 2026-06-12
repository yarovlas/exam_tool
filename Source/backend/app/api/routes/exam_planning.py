from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.exam_planning import Base, ExamPlanning


from app.schemas.exam_planning import ExamPlanningCreate, ExamPlanningRead, ExamPlanningUpdate


router = APIRouter(prefix="/exam-planning", tags=["exam-planning"])

EXAMPLE_EXAM = {
    "exam_date": date(2026, 6, 10),
    "exam_type": "practical",
    "room": "B101",
    "exam_time": time(9, 0),
    "status": "planned",
}


@router.post("", response_model=ExamPlanningRead, status_code=status.HTTP_201_CREATED)
def create_exam_planning(payload: ExamPlanningCreate, db: Session = Depends(get_db)) -> ExamPlanning:
    item = ExamPlanning(
        exam_date=payload.exam_date,
        exam_type=payload.exam_type,
        room=payload.room,
        exam_time=payload.exam_time,
        status=payload.status,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{exam_id}", response_model=ExamPlanningRead)
def update_exam_planning(
    exam_id: int,
    payload: ExamPlanningUpdate,
    db: Session = Depends(get_db),
) -> ExamPlanning:
    item = db.get(ExamPlanning, exam_id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam planning not found")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam_planning(exam_id: int, db: Session = Depends(get_db)) -> None:
    item = db.get(ExamPlanning, exam_id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam planning not found")

    db.delete(item)
    db.commit()


@router.post("/example", response_model=ExamPlanningRead, status_code=status.HTTP_201_CREATED)
def create_example_exam(db: Session = Depends(get_db)) -> ExamPlanning:
    Base.metadata.create_all(bind=db.get_bind())

    query = select(ExamPlanning).where(
        ExamPlanning.exam_date == EXAMPLE_EXAM["exam_date"],
        ExamPlanning.exam_type == EXAMPLE_EXAM["exam_type"],
        ExamPlanning.room == EXAMPLE_EXAM["room"],
        ExamPlanning.exam_time == EXAMPLE_EXAM["exam_time"],
    )
    existing = db.execute(query).scalars().first()
    if existing is not None:
        return existing

    item = ExamPlanning(**EXAMPLE_EXAM)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[ExamPlanningRead])
def list_exam_planning(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ExamPlanning]:
    query = (
        select(ExamPlanning)
        .order_by(ExamPlanning.exam_date.asc(), ExamPlanning.exam_time.asc(), ExamPlanning.id.asc())
        .limit(limit)
        .offset(offset)
    )
    items = db.execute(query).scalars().all()
    return list(items)

