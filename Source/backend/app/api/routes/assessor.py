from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.assessor import Assessor
from app.schemas.assessor import AssessorCreate, AssessorRead, AssessorUpdate


router = APIRouter(prefix="/assessors", tags=["assessors"])


@router.post("", response_model=AssessorRead, status_code=status.HTTP_201_CREATED)
def create_assessor(payload: AssessorCreate, db: Session = Depends(get_db)) -> Assessor:
    assessor = Assessor(
        assessor_type=payload.assessor_type,
        name=payload.name,
        organization=payload.organization,
        salutation=payload.salutation,
        address=payload.address,
        postal_city=payload.postal_city,
        phone=payload.phone,
        email=payload.email,
        recruitment_status=payload.recruitment_status,
    )

    db.add(assessor)
    db.commit()
    db.refresh(assessor)
    return assessor


@router.get("", response_model=list[AssessorRead])
def list_assessors(
    assessor_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Assessor]:
    query = select(Assessor)

    if assessor_type:
        query = query.where(Assessor.assessor_type == assessor_type)

    query = (
        query.order_by(Assessor.name.asc())
        .limit(limit)
        .offset(offset)
    )
    assessors = db.execute(query).scalars().all()
    return list(assessors)


@router.get("/{assessor_id}", response_model=AssessorRead)
def get_assessor(assessor_id: int, db: Session = Depends(get_db)) -> Assessor:
    assessor = db.get(Assessor, assessor_id)

    if assessor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessor not found")

    return assessor


@router.patch("/{assessor_id}", response_model=AssessorRead)
def update_assessor(
    assessor_id: int,
    payload: AssessorUpdate,
    db: Session = Depends(get_db),
) -> Assessor:
    assessor = db.get(Assessor, assessor_id)

    if assessor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessor not found")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(assessor, field, value)

    db.commit()
    db.refresh(assessor)
    return assessor


@router.delete("/{assessor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessor(assessor_id: int, db: Session = Depends(get_db)) -> None:
    assessor = db.get(Assessor, assessor_id)

    if assessor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessor not found")

    db.delete(assessor)
    db.commit()
