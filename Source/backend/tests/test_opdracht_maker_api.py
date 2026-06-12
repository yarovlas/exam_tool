"""
Integration tests voor de Opdracht Maker API routes.

Gebruikt een in-memory SQLite database en de FastAPI TestClient.
Geen echte PostgreSQL-verbinding nodig.

Gedekte scenario's:
  - GET /opdracht-maker/context/{id}
  - POST /opdracht-maker/calculate
  - POST /opdracht-maker/create
  - Bug #7: total_valid check bij create
  - Bug #5: 0-sterren surprise telt als geselecteerd
  - Ongeldige required-slots worden afgewezen
  - Dubbele producten worden gedetecteerd
"""

import pytest
from datetime import date, time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, StaticPool
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db
from app.models.exam_planning import Base, ExamPlanning
from app.models.student import Student
from app.models.exam_student import ExamStudent
from app.models.product import Product
from app.models.assignment import Assignment
from app.models.assignment_product import AssignmentProduct
from app.models.auth import AppAuth
from app.core.auth import hash_password

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///:memory:"


def make_engine():
    return create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="function")
def db():
    """Elke testfunctie krijgt een verse in-memory database."""
    engine = make_engine()
    Base.metadata.create_all(engine)

    # Importeer alle models zodat de tabellen aangemaakt worden
    import app.models  # noqa: F401

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(db):
    """TestClient met de in-memory database als dependency override."""
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app, raise_server_exceptions=True)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def seed_auth(db: Session) -> None:
    """Voeg een testgebruiker toe zodat de auth-endpoints werken."""
    auth = AppAuth(email="test@test.nl", password_hash=hash_password("testpass"))
    db.add(auth)
    db.commit()


def get_token(client: TestClient) -> str:
    resp = client.post("/api/auth/login", json={"email": "test@test.nl", "password": "testpass"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(client: TestClient) -> dict:
    token = get_token(client)
    return {"Authorization": f"Bearer {token}"}


def make_exam_student(
    db: Session,
    program_code: str = "ZWBA",
    student_phase: str = "Competent",
    exam_student_phase: str | None = None,
) -> ExamStudent:
    planning = ExamPlanning(
        exam_date=date(2026, 6, 15),      # Python date object (SQLite vereist dit)
        exam_type="practical",
        room="A01",
        exam_time=time(9, 0, 0),           # Python time object
        status="planned",
    )
    db.add(planning)
    db.flush()

    student = Student(
        student_number=f"S{program_code}{student_phase[:3]}{id(db)}",  # uniek per test
        name=f"Test Student {program_code}",
        program_code=program_code,
        phase=student_phase,
        email="student@test.nl",
    )
    db.add(student)
    db.flush()

    exam_student = ExamStudent(
        exam_planning_id=planning.id,
        student_id=student.id,
        phase=exam_student_phase,  # None = fallback naar student.phase
    )
    db.add(exam_student)
    db.commit()
    db.refresh(exam_student)
    return exam_student


def make_product(
    db: Session,
    name: str,
    speciality_code: str,
    category: str,
    stars: int,
    product_kind: str = "regular",
    document_link: str | None = None,
) -> Product:
    product = Product(
        product_kind=product_kind,
        speciality_code=speciality_code,
        speciality_name=None,
        name=name,
        category=category,
        stars=stars,
        document_link=document_link,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# ---------------------------------------------------------------------------
# Tests: GET /opdracht-maker/context
# ---------------------------------------------------------------------------


class TestGetContext:
    def test_returns_context_for_valid_exam_student(self, client, db):
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA")

        # Voeg een product toe dat hoort bij de eerste verplichte groep van ZWBA
        make_product(db, "Champagnetaart", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)

        resp = client.get(
            f"/api/opdracht-maker/context/{exam_student.id}",
            headers=auth_headers(client),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["exam_student_id"] == exam_student.id
        assert data["student"]["program_code"] == "ZWBA"
        assert "norm" in data
        assert data["norm"]["min_regular_stars"] == 9  # Competent
        assert data["norm"]["min_total_stars"] == 12
        assert len(data["required_groups"]) == 2
        assert len(data["choice_groups"]) == 3

    def test_returns_404_for_unknown_exam_student(self, client, db):
        seed_auth(db)
        resp = client.get("/api/opdracht-maker/context/9999", headers=auth_headers(client))
        assert resp.status_code == 404

    def test_returns_422_for_unknown_program_code(self, client, db):
        seed_auth(db)

        # Maak een student met een onbekend programmacode
        planning = ExamPlanning(
            exam_date=date(2026, 6, 15),
            exam_type="practical",
            room="A01",
            exam_time=time(9, 0, 0),
            status="planned",
        )
        db.add(planning)
        db.flush()
        student = Student(
            student_number="S_UNKNOWN",
            name="Unknown Student",
            program_code="ONBEKEND",
            phase="Competent",
        )
        db.add(student)
        db.flush()
        es = ExamStudent(exam_planning_id=planning.id, student_id=student.id, phase=None)
        db.add(es)
        db.commit()

        resp = client.get(
            f"/api/opdracht-maker/context/{es.id}",
            headers=auth_headers(client),
        )
        assert resp.status_code == 422

    def test_phase_fallback_from_student(self, client, db):
        """Als exam_student.phase NULL is, moet de norm gebaseerd zijn op student.phase."""
        seed_auth(db)
        # Gevorderd: min_regular=8, min_total=11
        exam_student = make_exam_student(
            db,
            program_code="ZWBA",
            student_phase="Gevorderd",
            exam_student_phase=None,  # geen override
        )

        resp = client.get(
            f"/api/opdracht-maker/context/{exam_student.id}",
            headers=auth_headers(client),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["norm"]["min_regular_stars"] == 8
        assert data["norm"]["min_total_stars"] == 11

    def test_alias_pat_resolves_to_zwbb_context(self, client, db):
        """
        PAT is een alias voor ZWBB. De context moet ZWBB-regels tonen
        en ZWBB-producten ophalen, ook al heeft de student program_code='PAT'.
        """
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="PAT", student_phase="Competent")
        # Voeg een ZWBB-product toe (want PAT → ZWBB)
        make_product(db, "Grootbrood 3*", "ZWBB", "Gistdeeg Ong. Grootbrood ZWBR en ZWBB", stars=3)

        resp = client.get(
            f"/api/opdracht-maker/context/{exam_student.id}",
            headers=auth_headers(client),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        # Moet ZWBB-normen gebruiken (Competent: 9, 12)
        assert data["norm"]["min_regular_stars"] == 9
        assert data["norm"]["min_total_stars"] == 12
        # Moet 2 required groups hebben (ZWBB heeft er 2)
        assert len(data["required_groups"]) == 2
        # Choice groups van ZWBB (3 stuks)
        assert len(data["choice_groups"]) == 3

    def test_alias_pat_can_create_assignment(self, client, db):
        """
        PAT-student moet een opdracht kunnen aanmaken met ZWBB-producten.
        """
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="PAT", student_phase="Competent")
        # ZWBB producten (PAT → ZWBB)
        p1 = make_product(db, "Gebak 3*", "ZWBB", "Gebak en taarten ZWBA en ZWBB", stars=3)
        p2 = make_product(db, "Grootbrood 3*", "ZWBB", "Gistdeeg Ong. Grootbrood ZWBR en ZWBB", stars=3)
        p3 = make_product(db, "Stukwerk beslag 3*", "ZWBB", "Stukwerk Beslag ZWBA/ZWBB", stars=3)
        surprise = make_product(db, "Verassing 3*", "ZWBB", None, stars=3, product_kind="surprise", document_link="x.xlsx")

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "required", "product_order": 2},
                {"product_id": p3.id, "product_role": "choice", "product_order": 1},
                {"product_id": surprise.id, "product_role": "surprise", "product_order": 1},
            ],
        }
        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["assignment"]["regular_stars"] == 9
        assert data["assignment"]["total_stars"] == 12
        assert len(data["assignment_products"]) == 4


# ---------------------------------------------------------------------------
# Tests: POST /opdracht-maker/calculate
# ---------------------------------------------------------------------------


class TestCalculate:
    def _make_zwba_products(self, db):
        """Maak minimale ZWBA-producten aan voor een geldig pakket."""
        p1 = make_product(db, "Champagnetaart 3*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)
        p2 = make_product(db, "Vormbonbons 3*", "ZWBA", "Chocolade ZWBA", stars=3)
        p3 = make_product(db, "Appelvictoria 3*", "ZWBA", "Stukwerk Zand ZWBA/ZWBB", stars=3)
        surprise = make_product(
            db, "Amandelluxe 3*", "ZWBA", None, stars=3, product_kind="surprise", document_link="x.xlsx"
        )
        return p1, p2, p3, surprise

    def test_calculate_valid_selection(self, client, db):
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1, p2, p3, surprise = self._make_zwba_products(db)

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "required", "product_order": 2},
                {"product_id": p3.id, "product_role": "choice", "product_order": 1},
                {"product_id": surprise.id, "product_role": "surprise", "product_order": 1},
            ],
        }
        resp = client.post("/api/opdracht-maker/calculate", json=payload, headers=auth_headers(client))
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["regular_stars"] == 9   # 3+3+3
        assert data["total_stars"] == 12    # 9 regular + 3 surprise
        assert data["regular_valid"] is True
        assert data["total_valid"] is True

    def test_calculate_insufficient_regular_stars(self, client, db):
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        # Maak producten met te weinig sterren
        p1 = make_product(db, "Klein gebakje 1*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=1)
        p2 = make_product(db, "Chocolaatje 1*", "ZWBA", "Chocolade ZWBA", stars=1)
        p3 = make_product(db, "Appeltaartje 1*", "ZWBA", "Stukwerk Zand ZWBA/ZWBB", stars=1)

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "required", "product_order": 2},
                {"product_id": p3.id, "product_role": "choice", "product_order": 1},
            ],
        }
        resp = client.post("/api/opdracht-maker/calculate", json=payload, headers=auth_headers(client))
        assert resp.status_code == 200
        data = resp.json()
        assert data["regular_stars"] == 3
        assert data["regular_valid"] is False  # 3 < 9 (min voor Competent)

    def test_calculate_zero_star_surprise_counts_as_selected(self, client, db):
        """
        Bug #5 fix: een 0-sterren surprise-product moet als 'geselecteerd' gelden.
        Vóór de fix zou total_stars = regular_stars + required_stars (i.p.v. + 0).
        """
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1, p2, p3, _ = self._make_zwba_products(db)
        # Maak een 0-sterren surprise
        zero_star_surprise = make_product(
            db, "Vrije keuze 0*", "ZWBA", None, stars=0, product_kind="surprise", document_link="x.xlsx"
        )

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "required", "product_order": 2},
                {"product_id": p3.id, "product_role": "choice", "product_order": 1},
                {"product_id": zero_star_surprise.id, "product_role": "surprise", "product_order": 1},
            ],
        }
        resp = client.post("/api/opdracht-maker/calculate", json=payload, headers=auth_headers(client))
        assert resp.status_code == 200
        data = resp.json()

        # Met fix: 9 regular + 0 surprise = 9 (surprise is geselecteerd, maar heeft 0 sterren)
        assert data["regular_stars"] == 9
        assert data["total_stars"] == 9  # 9 + 0 (niet 9 + required_stars!)
        assert data["total_valid"] is False  # 9 < 12

    def test_calculate_without_surprise_uses_required_stars_placeholder(self, client, db):
        """Zonder surprise-selectie is total_stars = regular + required_stars (placeholder)."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1, p2, p3, _ = self._make_zwba_products(db)

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "required", "product_order": 2},
                {"product_id": p3.id, "product_role": "choice", "product_order": 1},
            ],
        }
        resp = client.post("/api/opdracht-maker/calculate", json=payload, headers=auth_headers(client))
        assert resp.status_code == 200
        data = resp.json()

        # required_stars = max(0, 12 - 9) = 3
        assert data["required_stars"] == 3
        assert data["total_stars"] == 12  # 9 + 3 (placeholder)


# ---------------------------------------------------------------------------
# Tests: POST /opdracht-maker/create
# ---------------------------------------------------------------------------


class TestCreate:
    def _make_zwba_products(self, db):
        p1 = make_product(db, "Champagnetaart 3*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)
        p2 = make_product(db, "Vormbonbons 3*", "ZWBA", "Chocolade ZWBA", stars=3)
        p3 = make_product(db, "Appelvictoria 3*", "ZWBA", "Stukwerk Zand ZWBA/ZWBB", stars=3)
        surprise = make_product(
            db, "Amandelluxe 3*", "ZWBA", None, stars=3, product_kind="surprise", document_link="x.xlsx"
        )
        return p1, p2, p3, surprise

    def _valid_payload(self, exam_student_id, p1, p2, p3, surprise):
        return {
            "exam_student_id": exam_student_id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "required", "product_order": 2},
                {"product_id": p3.id, "product_role": "choice", "product_order": 1},
                {"product_id": surprise.id, "product_role": "surprise", "product_order": 1},
            ],
        }

    def test_create_valid_assignment(self, client, db):
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1, p2, p3, surprise = self._make_zwba_products(db)

        payload = self._valid_payload(exam_student.id, p1, p2, p3, surprise)
        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 201, resp.text
        data = resp.json()

        assert data["assignment"]["status"] == "confirmed"
        assert data["assignment"]["regular_stars"] == 9
        assert data["assignment"]["total_stars"] == 12
        # Moet 4 assignment-producten hebben (3 regular/choice + 1 surprise)
        assert len(data["assignment_products"]) == 4

    def test_create_as_confirmed(self, client, db):
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1, p2, p3, surprise = self._make_zwba_products(db)
        payload = {**self._valid_payload(exam_student.id, p1, p2, p3, surprise), "status": "confirmed"}

        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 201
        assert resp.json()["assignment"]["status"] == "confirmed"

    def test_create_fails_if_regular_stars_insufficient(self, client, db):
        """Bug #7 fix — eerste check: te weinig regular sterren."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1 = make_product(db, "Klein gebakje 1*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=1)
        p2 = make_product(db, "Chocolaatje 1*", "ZWBA", "Chocolade ZWBA", stars=1)
        p3 = make_product(db, "Appeltaartje 1*", "ZWBA", "Stukwerk Zand ZWBA/ZWBB", stars=1)
        surprise = make_product(
            db, "Grote verrassing 9*", "ZWBA", None, stars=9, product_kind="surprise", document_link="x.xlsx"
        )

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "required", "product_order": 2},
                {"product_id": p3.id, "product_role": "choice", "product_order": 1},
                {"product_id": surprise.id, "product_role": "surprise", "product_order": 1},
            ],
        }
        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 422
        assert "regular" in resp.json()["detail"].lower()

    def test_create_fails_if_total_stars_insufficient(self, client, db):
        """
        Bug #7 fix — tweede check: genoeg regular sterren maar te weinig totaal.
        ZWBA Competent: min_regular=9, min_total=12.
        We sturen 9 regular sterren + 0-sterren surprise → total=9 < 12.
        """
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1 = make_product(db, "Gebak 3*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)
        p2 = make_product(db, "Choco 3*", "ZWBA", "Chocolade ZWBA", stars=3)
        p3 = make_product(db, "Stukwerk 3*", "ZWBA", "Stukwerk Zand ZWBA/ZWBB", stars=3)
        zero_surprise = make_product(
            db, "Vrije keuze 0*", "ZWBA", None, stars=0, product_kind="surprise", document_link="x.xlsx"
        )

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "required", "product_order": 2},
                {"product_id": p3.id, "product_role": "choice", "product_order": 1},
                {"product_id": zero_surprise.id, "product_role": "surprise", "product_order": 1},
            ],
        }
        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 422, resp.text
        assert "total" in resp.json()["detail"].lower()

    def test_create_fails_if_total_stars_insufficient_without_surprise(self, client, db):
        """
        Als er géén surprise is geselecteerd maar total_stars (placeholder) al voldoende is
        via de berekening, dan mag create doorgaan.
        Dit test dat de placeholder-logica correct werkt.
        """
        seed_auth(db)
        # UBB heeft geen choice_groups — gebruik UBR dat ook eenvoudig is
        # UBR Competent: min_regular=5, min_total=8
        # We geven 5 regular sterren → placeholder required_stars = 3 → total = 8 ✓
        rules_ubr = make_exam_student(db, program_code="UBR", student_phase="Competent")
        p1 = make_product(db, "Gevuld kleinbrood 3*", "UBR", "Gevuld kleinbrood - UBR & UBB", stars=3)
        p2 = make_product(db, "Zacht kleinbrood 2*", "UBR", "Ongevuld Zacht kleinbrood - UBR", stars=2)

        payload = {
            "exam_student_id": rules_ubr.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "choice", "product_order": 1},
            ],
        }
        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["assignment"]["regular_stars"] == 5
        # Surprise als placeholder-product moet aangemaakt zijn
        surprise_products = [
            ap for ap in data["assignment_products"] if ap["product_role"] == "surprise"
        ]
        assert len(surprise_products) == 1
        assert "Minimaal" in surprise_products[0]["product_text"]

    def test_create_conflict_on_duplicate(self, client, db):
        """Twee keer hetzelfde product insturen geeft 422."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1 = make_product(db, "Champagnetaart 3*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p1.id, "product_role": "required", "product_order": 2},  # zelfde product!
            ],
        }
        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 422
        assert "more than once" in resp.json()["detail"].lower()

    def test_create_rejects_unknown_required_slot(self, client, db):
        """
        Bug fix: een required-slot dat niet bestaat in de programmaregels
        moet worden afgewezen (bijv. order=99 voor ZWBA dat alleen slots 1 en 2 heeft).
        """
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1 = make_product(db, "Gebak 3*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 99},  # ongeldig slot!
            ],
        }
        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 422
        assert "99" in resp.json()["detail"] or "valid" in resp.json()["detail"].lower()

    def test_create_existing_assignment_rejected_without_replace(self, client, db):
        """Een tweede create voor hetzelfde exam-student geeft 409 zonder replace_existing."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1, p2, p3, surprise = self._make_zwba_products(db)
        payload = self._valid_payload(exam_student.id, p1, p2, p3, surprise)

        resp1 = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp1.status_code == 201

        resp2 = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp2.status_code == 409

    def test_create_replaces_existing_assignment(self, client, db):
        """Met replace_existing=True moet het bestaande opdracht vervangen worden."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1, p2, p3, surprise = self._make_zwba_products(db)
        payload = self._valid_payload(exam_student.id, p1, p2, p3, surprise)

        resp1 = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp1.status_code == 201
        assignment_id_1 = resp1.json()["assignment"]["id"]

        payload_replace = {**payload, "replace_existing": True}
        resp2 = client.post("/api/opdracht-maker/create", json=payload_replace, headers=auth_headers(client))
        assert resp2.status_code == 201

        # Het tweede create moet slagen en een volledig nieuw pakket hebben
        data2 = resp2.json()
        assert data2["assignment"]["regular_stars"] == 9
        assert data2["assignment"]["total_stars"] == 12
        assert len(data2["assignment_products"]) == 4

        # Controleer dat het tweede assign-object ook correct is opgeslagen
        resp_check = client.get(
            f"/api/assignments?exam_student_id={exam_student.id}",
            headers=auth_headers(client),
        )
        assert resp_check.status_code == 200
        assignments = resp_check.json()
        # Er mag maar 1 assignment zijn voor deze exam_student (uniqueness constraint)
        assert len(assignments) == 1

    def test_create_without_surprise_adds_placeholder(self, client, db):
        """
        Als er geen surprise is geselecteerd, moet er automatisch een placeholder
        AssignmentProduct aangemaakt worden met product_text='Minimaal X*'.
        """
        seed_auth(db)
        # UBB heeft geen choice-groepen — 2 required verplicht
        exam_student = make_exam_student(db, program_code="UBB", student_phase="Competent")
        p1 = make_product(db, "Gevuld kleinbrood 3*", "UBB", "Gevuld kleinbrood - UBR & UBB", stars=3)
        p2 = make_product(db, "Taart 3*", "UBB", "Gebak en taarten UBB & UBA", stars=3)

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": p1.id, "product_role": "required", "product_order": 1},
                {"product_id": p2.id, "product_role": "required", "product_order": 2},
            ],
        }
        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 201, resp.text
        data = resp.json()

        surprise_products = [
            ap for ap in data["assignment_products"] if ap["product_role"] == "surprise"
        ]
        assert len(surprise_products) == 1
        assert surprise_products[0]["product_id"] is None
        assert "Minimaal" in surprise_products[0]["product_text"]

    def test_create_wrong_program_product_rejected(self, client, db):
        """Een product dat bij een ander programma hoort mag niet worden gebruikt."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        # Product behoort tot UBA — niet ZWBA
        wrong_product = make_product(db, "UBA Product 3*", "UBA", "Gebak en taarten UBB & UBA", stars=3)

        payload = {
            "exam_student_id": exam_student.id,
            "products": [
                {"product_id": wrong_product.id, "product_role": "required", "product_order": 1},
            ],
        }
        resp = client.post("/api/opdracht-maker/create", json=payload, headers=auth_headers(client))
        assert resp.status_code == 422
        assert "program code" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Tests: POST /opdracht-maker/batch/auto-assign-surprises
# ---------------------------------------------------------------------------


def _make_assignment_with_placeholder(
    db: Session,
    exam_student: ExamStudent,
    p1, p2, p3,
    status: str = "confirmed",
) -> int:
    """Create an assignment with required+choice but NO surprise (creates placeholder)."""
    assignment = Assignment(
        exam_student_id=exam_student.id,
        status=status,
        regular_stars=p1.stars + p2.stars + p3.stars,
        required_stars=3,
        total_stars=p1.stars + p2.stars + p3.stars + 3,
    )
    db.add(assignment)
    db.flush()

    for role, order, product in [
        ("required", 1, p1),
        ("required", 2, p2),
        ("choice", 1, p3),
    ]:
        ap = AssignmentProduct(
            assignment_id=assignment.id,
            product_id=product.id,
            product_role=role,
            product_order=order,
            stars=product.stars,
        )
        db.add(ap)

    placeholder = AssignmentProduct(
        assignment_id=assignment.id,
        product_id=None,
        product_role="surprise",
        product_order=1,
        product_text="Minimaal 3*",
        stars=3,
    )
    db.add(placeholder)
    db.commit()
    return assignment.id


class TestAutoAssignSurprises:
    def test_auto_assign_fills_placeholder(self, client, db):
        """Placeholder surprise moet worden gevuld met een echt product."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1 = make_product(db, "Gebak 3*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)
        p2 = make_product(db, "Choco 3*", "ZWBA", "Chocolade ZWBA", stars=3)
        p3 = make_product(db, "Stukwerk 3*", "ZWBA", "Stukwerk Zand ZWBA/ZWBB", stars=3)
        _make_assignment_with_placeholder(db, exam_student, p1, p2, p3)

        # Maak een surprise-product beschikbaar
        surprise = make_product(
            db, "Verassing 3*", "ZWBA", None, stars=3, product_kind="surprise", document_link="x.xlsx"
        )

        payload = {"exam_planning_id": exam_student.exam_planning_id}
        resp = client.post(
            "/api/opdracht-maker/batch/auto-assign-surprises",
            json=payload,
            headers=auth_headers(client),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["total"] == 1
        assert data["updated"] == 1
        assert data["skipped_no_assignment"] == 0
        assert data["skipped_already_assigned"] == 0
        assert data["skipped_no_match"] == 0
        assert len(data["errors"]) == 0

        # Controleer dat de surprise is toegewezen
        item = data["results"][0]
        assert item["surprise_product"]["id"] == surprise.id
        assert item["surprise_product"]["stars"] == 3
        # Controleer regular_stars en available_surprises
        assert item["regular_stars"] == 9
        assert item["required_stars"] == 3
        assert len(item["available_surprises"]) == 1
        assert item["available_surprises"][0]["id"] == surprise.id

        # Controleer in de database
        db_surprise = db.execute(
            select(AssignmentProduct)
            .join(Assignment)
            .where(
                Assignment.exam_student_id == exam_student.id,
                AssignmentProduct.product_role == "surprise",
            )
        ).scalars().first()
        assert db_surprise.product_id == surprise.id
        assert db_surprise.product_text is None
        assert db_surprise.stars == 3

    def test_auto_assign_skips_no_assignment(self, client, db):
        """Student zonder assignment moet worden overgeslagen."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")

        payload = {"exam_planning_id": exam_student.exam_planning_id}
        resp = client.post(
            "/api/opdracht-maker/batch/auto-assign-surprises",
            json=payload,
            headers=auth_headers(client),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["updated"] == 0
        assert data["skipped_no_assignment"] == 1

    def test_auto_assign_skips_already_assigned(self, client, db):
        """Student die al een echte surprise heeft moet worden overgeslagen."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1 = make_product(db, "Gebak 3*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)
        p2 = make_product(db, "Choco 3*", "ZWBA", "Chocolade ZWBA", stars=3)
        p3 = make_product(db, "Stukwerk 3*", "ZWBA", "Stukwerk Zand ZWBA/ZWBB", stars=3)
        ass_id = _make_assignment_with_placeholder(db, exam_student, p1, p2, p3)
        surprise = make_product(
            db, "Verassing 3*", "ZWBA", None, stars=3, product_kind="surprise", document_link="x.xlsx"
        )

        # Wijs de surprise alvast toe (alsof het in een eerdere run is gebeurd)
        db_surprise = db.execute(
            select(AssignmentProduct).where(
                AssignmentProduct.assignment_id == ass_id,
                AssignmentProduct.product_role == "surprise",
            )
        ).scalars().first()
        db_surprise.product_id = surprise.id
        db_surprise.product_text = None
        db_surprise.stars = surprise.stars
        db.commit()

        payload = {"exam_planning_id": exam_student.exam_planning_id}
        resp = client.post(
            "/api/opdracht-maker/batch/auto-assign-surprises",
            json=payload,
            headers=auth_headers(client),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["updated"] == 0
        assert data["skipped_already_assigned"] == 1

    def test_auto_assign_skips_no_match(self, client, db):
        """Geen passende surprise producten → skip."""
        seed_auth(db)
        exam_student = make_exam_student(db, program_code="ZWBA", student_phase="Competent")
        p1 = make_product(db, "Gebak 3*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)
        p2 = make_product(db, "Choco 3*", "ZWBA", "Chocolade ZWBA", stars=3)
        p3 = make_product(db, "Stukwerk 3*", "ZWBA", "Stukwerk Zand ZWBA/ZWBB", stars=3)
        _make_assignment_with_placeholder(db, exam_student, p1, p2, p3)

        # Geen surprise-producten voor ZWBA
        payload = {"exam_planning_id": exam_student.exam_planning_id}
        resp = client.post(
            "/api/opdracht-maker/batch/auto-assign-surprises",
            json=payload,
            headers=auth_headers(client),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["updated"] == 0
        assert data["skipped_no_match"] == 1

    def test_auto_assign_filters_by_exam_student_ids(self, client, db):
        """Alleen gespecificeerde studenten verwerken."""
        seed_auth(db)
        planning = ExamPlanning(
            exam_date=date(2026, 6, 15),
            exam_type="practical",
            room="A01",
            exam_time=time(9, 0, 0),
            status="planned",
        )
        db.add(planning)
        db.flush()

        def make_es(program_code):
            student = Student(
                student_number=f"S{program_code}_{id(planning)}",
                name=f"Student {program_code}",
                program_code=program_code,
                phase="Competent",
                email="s@test.nl",
            )
            db.add(student)
            db.flush()
            es = ExamStudent(exam_planning_id=planning.id, student_id=student.id, phase=None)
            db.add(es)
            db.flush()
            return es

        es1 = make_es("ZWBA")
        es2 = make_es("ZWBB")

        # Alleen de eerste verwerken
        payload = {
            "exam_planning_id": planning.id,
            "exam_student_ids": [es1.id],
        }
        resp = client.post(
            "/api/opdracht-maker/batch/auto-assign-surprises",
            json=payload,
            headers=auth_headers(client),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1  # maar 1 van de 2

    def test_auto_assign_batch_multiple_students(self, client, db):
        """Meerdere studenten tegelijk verwerken (zelfde planning)."""
        seed_auth(db)
        planning = ExamPlanning(
            exam_date=date(2026, 6, 15),
            exam_type="practical",
            room="A01",
            exam_time=time(9, 0, 0),
            status="planned",
        )
        db.add(planning)
        db.flush()

        def make_es(program_code, phase):
            student = Student(
                student_number=f"S{program_code}_{id(planning)}_{id(db)}",
                name=f"Student {program_code}",
                program_code=program_code,
                phase=phase,
                email="s@test.nl",
            )
            db.add(student)
            db.flush()
            es = ExamStudent(exam_planning_id=planning.id, student_id=student.id, phase=None)
            db.add(es)
            db.flush()
            return es, student

        es1, _ = make_es("ZWBA", "Competent")
        es2, _ = make_es("UBB", "Competent")

        p1 = make_product(db, "Gebak 3*", "ZWBA", "Gebak en taarten ZWBA en ZWBB", stars=3)
        p2 = make_product(db, "Choco 3*", "ZWBA", "Chocolade ZWBA", stars=3)
        p3 = make_product(db, "Stukwerk 3*", "ZWBA", "Stukwerk Zand ZWBA/ZWBB", stars=3)
        _make_assignment_with_placeholder(db, es1, p1, p2, p3)

        p4 = make_product(db, "Gevuld 3*", "UBB", "Gevuld kleinbrood - UBR & UBB", stars=3)
        p5 = make_product(db, "Taart 2*", "UBB", "Gebak en taarten UBB & UBA", stars=2)
        assignment2 = Assignment(
            exam_student_id=es2.id,
            status="confirmed",
            regular_stars=p4.stars + p5.stars,
            required_stars=3,
            total_stars=8,
        )
        db.add(assignment2)
        db.flush()
        for role, order, product in [("required", 1, p4), ("required", 2, p5)]:
            db.add(AssignmentProduct(
                assignment_id=assignment2.id,
                product_id=product.id,
                product_role=role,
                product_order=order,
                stars=product.stars,
            ))
        db.add(AssignmentProduct(
            assignment_id=assignment2.id,
            product_id=None,
            product_role="surprise",
            product_order=1,
            product_text="Minimaal 3*",
            stars=3,
        ))
        db.commit()

        make_product(db, "Verassing ZW 3*", "ZWBA", None, stars=3, product_kind="surprise", document_link="x.xlsx")
        make_product(db, "Verassing UB 3*", "UBB", None, stars=3, product_kind="surprise", document_link="x.xlsx")

        payload = {"exam_planning_id": planning.id}
        resp = client.post(
            "/api/opdracht-maker/batch/auto-assign-surprises",
            json=payload,
            headers=auth_headers(client),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["updated"] == 2
        assert data["skipped_no_assignment"] == 0
        assert data["skipped_already_assigned"] == 0
        assert data["skipped_no_match"] == 0
        assert len(data["errors"]) == 0
