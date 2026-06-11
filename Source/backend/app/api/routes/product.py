from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.assignment_product import AssignmentProduct
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    product = Product(
        product_kind=payload.product_kind,
        speciality_code=payload.speciality_code,
        speciality_name=payload.speciality_name,
        name=payload.name,
        category=payload.category,
        stars=payload.stars,
        document_link=payload.document_link,
    )

    db.add(product)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with the same kind, speciality code, and name already exists",
        ) from exc

    db.refresh(product)
    return product


@router.get("", response_model=list[ProductRead])
def list_products(
    product_kind: Optional[str] = Query(default=None),
    speciality_code: Optional[str] = Query(default=None),
    name: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Product]:
    query = select(Product)

    if product_kind is not None:
        query = query.where(Product.product_kind == product_kind)

    if speciality_code is not None:
        query = query.where(Product.speciality_code == speciality_code)

    if name is not None:
        query = query.where(Product.name.ilike(f"%{name}%"))

    if category is not None:
        query = query.where(Product.category.ilike(f"%{category}%"))

    query = query.order_by(Product.id.asc()).limit(limit).offset(offset)
    items = db.execute(query).scalars().all()
    return list(items)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    return product


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with the same kind, speciality code, and name already exists",
        ) from exc

    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    query = select(AssignmentProduct).where(AssignmentProduct.product_id == product_id)
    assignment_exists = db.execute(query).first() is not None

    if assignment_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete product associated with an assignment",
        )

    try:
        db.delete(product)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete product associated with an assignment",
        ) from exc
