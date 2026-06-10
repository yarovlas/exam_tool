from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.assignment_product import AssignmentProduct
from app.models.exam_student import ExamStudent
from app.models.product import Product
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentProductCreate,
    AssignmentProductRead,
    AssignmentProductUpdate,
    AssignmentRead,
    AssignmentUpdate,
)

router = APIRouter(tags=["assignments"])


def require_assignment_product_target(product_id: Optional[int], product_text: Optional[str]) -> None:
    if product_id is None and not product_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either product_id or product_text is required",
        )


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db)) -> Assignment:
    exam_student = db.get(ExamStudent, payload.exam_student_id)

    if exam_student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam-student link not found")

    assignment = Assignment(
        exam_student_id=payload.exam_student_id,
        status=payload.status,
        regular_stars=payload.regular_stars,
        required_stars=payload.required_stars,
        total_stars=payload.total_stars,
        result=payload.result,
    )

    db.add(assignment)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignment already exists for this exam-student link",
        ) from exc

    db.refresh(assignment)
    return assignment


@router.get("/assignments", response_model=list[AssignmentRead])
def list_assignments(
    exam_student_id: Optional[int] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Assignment]:
    query = select(Assignment)

    if exam_student_id is not None:
        query = query.where(Assignment.exam_student_id == exam_student_id)

    if status_filter:
        query = query.where(Assignment.status == status_filter)

    query = query.order_by(Assignment.id.asc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    return list(items)


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)) -> Assignment:
    assignment = db.get(Assignment, assignment_id)

    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    return assignment


@router.patch("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
) -> Assignment:
    assignment = db.get(Assignment, assignment_id)

    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)) -> None:
    assignment = db.get(Assignment, assignment_id)

    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    db.delete(assignment)
    db.commit()


@router.post(
    "/assignment-products",
    response_model=AssignmentProductRead,
    status_code=status.HTTP_201_CREATED,
    tags=["assignment-products"],
)
def create_assignment_product(
    payload: AssignmentProductCreate,
    db: Session = Depends(get_db),
) -> AssignmentProduct:
    assignment = db.get(Assignment, payload.assignment_id)

    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if payload.product_id is not None and db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    require_assignment_product_target(payload.product_id, payload.product_text)

    assignment_product = AssignmentProduct(
        assignment_id=payload.assignment_id,
        product_id=payload.product_id,
        product_role=payload.product_role,
        product_order=payload.product_order,
        product_text=payload.product_text,
        stars=payload.stars,
        result=payload.result,
    )

    db.add(assignment_product)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignment product conflicts with an existing assignment product",
        ) from exc

    db.refresh(assignment_product)
    return assignment_product


@router.get("/assignment-products", response_model=list[AssignmentProductRead], tags=["assignment-products"])
def list_assignment_products(
    assignment_id: Optional[int] = Query(default=None),
    product_id: Optional[int] = Query(default=None),
    product_role: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[AssignmentProduct]:
    query = select(AssignmentProduct)

    if assignment_id is not None:
        query = query.where(AssignmentProduct.assignment_id == assignment_id)

    if product_id is not None:
        query = query.where(AssignmentProduct.product_id == product_id)

    if product_role:
        query = query.where(AssignmentProduct.product_role == product_role)

    query = query.order_by(AssignmentProduct.assignment_id.asc(), AssignmentProduct.product_order.asc())
    query = query.limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    return list(items)


@router.get(
    "/assignment-products/{assignment_product_id}",
    response_model=AssignmentProductRead,
    tags=["assignment-products"],
)
def get_assignment_product(assignment_product_id: int, db: Session = Depends(get_db)) -> AssignmentProduct:
    assignment_product = db.get(AssignmentProduct, assignment_product_id)

    if assignment_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment product not found")

    return assignment_product


@router.patch(
    "/assignment-products/{assignment_product_id}",
    response_model=AssignmentProductRead,
    tags=["assignment-products"],
)
def update_assignment_product(
    assignment_product_id: int,
    payload: AssignmentProductUpdate,
    db: Session = Depends(get_db),
) -> AssignmentProduct:
    assignment_product = db.get(AssignmentProduct, assignment_product_id)

    if assignment_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment product not found")

    updates = payload.model_dump(exclude_unset=True)

    if "product_id" in updates and updates["product_id"] is not None and db.get(Product, updates["product_id"]) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for field, value in updates.items():
        setattr(assignment_product, field, value)

    require_assignment_product_target(assignment_product.product_id, assignment_product.product_text)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignment product conflicts with an existing assignment product",
        ) from exc

    db.refresh(assignment_product)
    return assignment_product


@router.delete("/assignment-products/{assignment_product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment_product(assignment_product_id: int, db: Session = Depends(get_db)) -> None:
    assignment_product = db.get(AssignmentProduct, assignment_product_id)

    if assignment_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment product not found")

    db.delete(assignment_product)
    db.commit()
