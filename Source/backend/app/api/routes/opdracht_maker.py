from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.assignment import Assignment
from app.models.assignment_product import AssignmentProduct
from app.models.exam_planning import ExamPlanning
from app.models.exam_student import ExamStudent
from app.models.product import Product
from app.schemas.opdracht_maker import (
    OpdrachtMakerCalculateRead,
    OpdrachtMakerCalculateRequest,
    OpdrachtMakerContextRead,
    OpdrachtMakerCreateRead,
    OpdrachtMakerCreateRequest,
    OpdrachtMakerExamRead,
    OpdrachtMakerNormRead,
    OpdrachtMakerProductGroupRead,
    OpdrachtMakerSelection,
    OpdrachtMakerStudentRead,
)
from app.services.opdracht_maker import ProductGroupRule, get_program_rules, get_star_norms

router = APIRouter(prefix="/opdracht-maker", tags=["opdracht-maker"])


def get_exam_student_or_404(exam_student_id: int, db: Session) -> ExamStudent:
    exam_student = db.get(ExamStudent, exam_student_id)

    if exam_student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam-student link not found")

    return exam_student


def get_rules_or_422(program_code: str):
    rules = get_program_rules(program_code)

    if rules is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No opdracht-maker rules configured for program code '{program_code}'",
        )

    return rules


def get_student_read(exam_student: ExamStudent) -> OpdrachtMakerStudentRead:
    student = exam_student.student
    # phase op exam_student is nullable — val terug op student.phase
    resolved_phase = exam_student.phase or student.phase
    return OpdrachtMakerStudentRead(
        id=exam_student.id,
        student_id=student.id,
        student_number=student.student_number,
        name=student.name,
        program_code=student.program_code,
        phase=resolved_phase,
        email=student.email,
        placement_group=student.placement_group,
    )


def get_exam_read(exam_planning: ExamPlanning) -> OpdrachtMakerExamRead:
    return OpdrachtMakerExamRead(
        id=exam_planning.id,
        exam_date=exam_planning.exam_date,
        exam_type=exam_planning.exam_type,
        room=exam_planning.room,
        exam_time=exam_planning.exam_time,
        status=exam_planning.status,
    )


def list_products_for_group(db: Session, program_code: str, group: ProductGroupRule) -> list[Product]:
    if group.category is None:
        return []

    query = (
        select(Product)
        .where(
            Product.product_kind == "regular",
            Product.speciality_code == program_code,
            Product.category == group.category,
        )
        .order_by(Product.stars.asc().nulls_last(), Product.name.asc())
    )
    return list(db.execute(query).scalars().all())


def list_used_product_ids(db: Session, exam_student: ExamStudent) -> list[int]:
    query = (
        select(AssignmentProduct.product_id)
        .join(Assignment)
        .join(ExamStudent)
        .where(
            ExamStudent.student_id == exam_student.student_id,
            ExamStudent.id != exam_student.id,
            AssignmentProduct.product_id.is_not(None),
        )
    )
    return [product_id for product_id in db.execute(query).scalars().all() if product_id is not None]


def get_products_by_id(db: Session, product_ids: list[int]) -> dict[int, Product]:
    if not product_ids:
        return {}

    products = db.execute(select(Product).where(Product.id.in_(product_ids))).scalars().all()
    found = {product.id: product for product in products}
    missing = sorted(set(product_ids) - set(found))

    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Products not found: {', '.join(str(product_id) for product_id in missing)}",
        )

    return found


def get_rule_for_selection(rules, selection: OpdrachtMakerSelection) -> ProductGroupRule | None:
    if selection.product_role == "required":
        return next(
            (group for group in rules.required_groups if group.order == selection.product_order),
            None,
        )

    # FIX: choice-sloten hebben altijd order=1, maar we zoeken op category (niet op None)
    # zodat we straks ook de category kunnen valideren
    if selection.product_role == "choice":
        return next(
            (group for group in rules.choice_groups if group.category is not None),
            None,
        )

    return None


def validate_selection(
    exam_student: ExamStudent,
    selections: list[OpdrachtMakerSelection],
    products_by_id: dict[int, Product],
) -> None:
    rules = get_rules_or_422(exam_student.student.program_code)
    program_code = exam_student.student.program_code
    seen_ids: set[int] = set()
    seen_slots: set[tuple[str, int]] = set()

    # Bepaal welke required-slots geldig zijn voor dit programma
    valid_required_orders = {group.order for group in rules.required_groups}

    for selection in selections:
        if selection.product_id in seen_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Product {selection.product_id} is selected more than once",
            )
        seen_ids.add(selection.product_id)

        slot = (selection.product_role, selection.product_order)
        if slot in seen_slots:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Duplicate assignment slot: {selection.product_role} {selection.product_order}",
            )
        seen_slots.add(slot)

        product = products_by_id[selection.product_id]

        if product.speciality_code != program_code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Product {product.id} does not belong to program code {program_code}",
            )

        if selection.product_role == "surprise":
            if product.product_kind != "surprise":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Product {product.id} is not a surprise product",
                )
            continue

        if product.product_kind != "regular":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Product {product.id} is not a regular product",
            )

        if selection.product_role == "required":
            # FIX: reject required slots that don't exist in the program rules
            if selection.product_order not in valid_required_orders:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Required slot {selection.product_order} is not valid for program {program_code}",
                )

            rule = get_rule_for_selection(rules, selection)
            if rule is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Required slot {selection.product_order} is not allowed for {program_code}",
                )

            if product.category != rule.category:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Product {product.id} must be from category '{rule.category}'",
                )

        if selection.product_role == "choice":
            allowed_categories = {group.category for group in rules.choice_groups}
            if product.category not in allowed_categories:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Product {product.id} is not in an allowed choice category",
                )

    required_slots = {("required", group.order) for group in rules.required_groups}
    missing_required = sorted(order for role, order in required_slots - seen_slots if role == "required")
    if missing_required:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required product slot(s): {', '.join(str(order) for order in missing_required)}",
        )

    if rules.choice_groups and ("choice", 1) not in seen_slots:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing choice product",
        )


def calculate_opdracht(
    exam_student: ExamStudent,
    selections: list[OpdrachtMakerSelection],
    products_by_id: dict[int, Product],
    db: Session,
) -> OpdrachtMakerCalculateRead:
    program_code = exam_student.student.program_code
    phase = exam_student.phase or exam_student.student.phase
    min_regular_stars, min_total_stars = get_star_norms(program_code, phase)

    regular_stars = sum(
        products_by_id[selection.product_id].stars or 0
        for selection in selections
        if selection.product_role in {"required", "choice"}
    )

    # FIX: gebruik een expliciete vlag i.p.v. sterren-som om te detecteren of een
    # surprise-product is geselecteerd. Een 0-sterren surprise telt ook mee.
    surprise_selections = [s for s in selections if s.product_role == "surprise"]
    has_selected_surprise = len(surprise_selections) > 0
    selected_surprise_stars = sum(
        products_by_id[selection.product_id].stars or 0
        for selection in surprise_selections
    )

    required_stars = max(0, min_total_stars - regular_stars)

    # Als de gebruiker een surprise heeft gekozen, gebruik die sterren;
    # anders tellen we de berekende eis (required_stars) als placeholder.
    total_stars = regular_stars + (selected_surprise_stars if has_selected_surprise else required_stars)

    used_product_ids = set(list_used_product_ids(db, exam_student))
    duplicate_product_ids = sorted(used_product_ids.intersection(products_by_id))
    suggestion_stars = max(1, required_stars)

    exact_suggestions = db.execute(
        select(Product)
        .where(
            Product.product_kind == "surprise",
            Product.speciality_code == program_code,
            Product.stars == suggestion_stars,
        )
        .order_by(Product.name.asc())
        .limit(200)
    ).scalars().all()

    if exact_suggestions:
        surprise_suggestions = list(exact_suggestions)
    else:
        surprise_suggestions = list(
            db.execute(
                select(Product)
                .where(
                    Product.product_kind == "surprise",
                    Product.speciality_code == program_code,
                    Product.stars >= suggestion_stars,
                )
                .order_by(Product.stars.asc(), Product.name.asc())
                .limit(200)
            ).scalars().all()
        )

    return OpdrachtMakerCalculateRead(
        regular_stars=regular_stars,
        required_stars=required_stars,
        total_stars=total_stars,
        min_regular_stars=min_regular_stars,
        min_total_stars=min_total_stars,
        regular_valid=regular_stars >= min_regular_stars,
        total_valid=total_stars >= min_total_stars,
        duplicate_product_ids=duplicate_product_ids,
        surprise_suggestions=surprise_suggestions,
    )


@router.get("/context/{exam_student_id}", response_model=OpdrachtMakerContextRead)
def get_opdracht_maker_context(exam_student_id: int, db: Session = Depends(get_db)) -> OpdrachtMakerContextRead:
    exam_student = get_exam_student_or_404(exam_student_id, db)
    program_code = exam_student.student.program_code
    phase = exam_student.phase or exam_student.student.phase
    rules = get_rules_or_422(program_code)
    min_regular_stars, min_total_stars = get_star_norms(program_code, phase)

    required_groups = [
        OpdrachtMakerProductGroupRead(
            role=group.role,
            order=group.order,
            label=group.label,
            category=group.category,
            products=list_products_for_group(db, program_code, group),
        )
        for group in rules.required_groups
    ]
    choice_groups = [
        OpdrachtMakerProductGroupRead(
            role=group.role,
            order=group.order,
            label=group.label,
            category=group.category,
            products=list_products_for_group(db, program_code, group),
        )
        for group in rules.choice_groups
    ]

    return OpdrachtMakerContextRead(
        exam_student_id=exam_student.id,
        student=get_student_read(exam_student),
        exam=get_exam_read(exam_student.exam_planning),
        norm=OpdrachtMakerNormRead(
            min_regular_stars=min_regular_stars,
            min_total_stars=min_total_stars,
        ),
        required_groups=required_groups,
        choice_groups=choice_groups,
        used_product_ids=list_used_product_ids(db, exam_student),
    )


@router.get("/context/{exam_id}/{student_id}", response_model=OpdrachtMakerContextRead)
def get_opdracht_maker_context_by_exam_student(
    exam_id: int,
    student_id: int,
    db: Session = Depends(get_db),
) -> OpdrachtMakerContextRead:
    exam_student = db.execute(
        select(ExamStudent).where(
            ExamStudent.exam_planning_id == exam_id,
            ExamStudent.student_id == student_id,
        )
    ).scalars().first()

    if exam_student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not linked to this exam",
        )

    program_code = exam_student.student.program_code
    phase = exam_student.phase or exam_student.student.phase
    rules = get_rules_or_422(program_code)
    min_regular_stars, min_total_stars = get_star_norms(program_code, phase)

    required_groups = [
        OpdrachtMakerProductGroupRead(
            role=group.role,
            order=group.order,
            label=group.label,
            category=group.category,
            products=list_products_for_group(db, program_code, group),
        )
        for group in rules.required_groups
    ]
    choice_groups = [
        OpdrachtMakerProductGroupRead(
            role=group.role,
            order=group.order,
            label=group.label,
            category=group.category,
            products=list_products_for_group(db, program_code, group),
        )
        for group in rules.choice_groups
    ]

    return OpdrachtMakerContextRead(
        exam_student_id=exam_student.id,
        student=get_student_read(exam_student),
        exam=get_exam_read(exam_student.exam_planning),
        norm=OpdrachtMakerNormRead(
            min_regular_stars=min_regular_stars,
            min_total_stars=min_total_stars,
        ),
        required_groups=required_groups,
        choice_groups=choice_groups,
        used_product_ids=list_used_product_ids(db, exam_student),
    )


@router.post("/calculate", response_model=OpdrachtMakerCalculateRead)
def calculate_opdracht_maker(
    payload: OpdrachtMakerCalculateRequest,
    db: Session = Depends(get_db),
) -> OpdrachtMakerCalculateRead:
    exam_student = get_exam_student_or_404(payload.exam_student_id, db)
    products_by_id = get_products_by_id(db, [selection.product_id for selection in payload.products])
    validate_selection(exam_student, payload.products, products_by_id)
    return calculate_opdracht(exam_student, payload.products, products_by_id, db)


@router.post("/create", response_model=OpdrachtMakerCreateRead, status_code=status.HTTP_201_CREATED)
def create_opdracht_from_maker(
    payload: OpdrachtMakerCreateRequest,
    db: Session = Depends(get_db),
) -> OpdrachtMakerCreateRead:
    exam_student = get_exam_student_or_404(payload.exam_student_id, db)
    products_by_id = get_products_by_id(db, [selection.product_id for selection in payload.products])
    validate_selection(exam_student, payload.products, products_by_id)
    calculation = calculate_opdracht(exam_student, payload.products, products_by_id, db)

    if not calculation.regular_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Regular/choice products have {calculation.regular_stars}★ but minimum is {calculation.min_regular_stars}★",
        )

    # FIX: controleer ook de totale sterren-norm (regular + surprise)
    if not calculation.total_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Total stars {calculation.total_stars}★ do not meet the minimum of {calculation.min_total_stars}★",
        )

    if calculation.duplicate_product_ids and not payload.allow_reuse:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product(s) already used for this student: {', '.join(str(i) for i in calculation.duplicate_product_ids)}",
        )

    existing_assignment = db.execute(
        select(Assignment).where(Assignment.exam_student_id == exam_student.id)
    ).scalars().first()

    if existing_assignment is not None and not payload.replace_existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assignment already exists for this exam-student link",
        )

    if existing_assignment is not None:
        db.delete(existing_assignment)
        db.flush()

    assignment = Assignment(
        exam_student_id=exam_student.id,
        status=payload.status,
        regular_stars=calculation.regular_stars,
        required_stars=calculation.required_stars,
        total_stars=calculation.total_stars,
    )
    db.add(assignment)
    db.flush()

    assignment_products: list[AssignmentProduct] = []
    for selection in payload.products:
        product = products_by_id[selection.product_id]
        assignment_product = AssignmentProduct(
            assignment_id=assignment.id,
            product_id=product.id,
            product_role=selection.product_role,
            product_order=selection.product_order,
            product_text=None,
            stars=product.stars,
        )
        db.add(assignment_product)
        assignment_products.append(assignment_product)

    has_surprise_product = any(selection.product_role == "surprise" for selection in payload.products)
    if not has_surprise_product:
        surprise_requirement = AssignmentProduct(
            assignment_id=assignment.id,
            product_id=None,
            product_role="surprise",
            product_order=1,
            product_text=f"Minimaal {calculation.required_stars}*",
            stars=calculation.required_stars,
        )
        db.add(surprise_requirement)
        assignment_products.append(surprise_requirement)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Could not create opdracht-maker assignment",
        ) from exc

    db.refresh(assignment)
    for assignment_product in assignment_products:
        db.refresh(assignment_product)

    return OpdrachtMakerCreateRead(
        assignment=assignment,
        assignment_products=assignment_products,
        calculation=calculation,
    )
