# Backend (FastAPI + PostgreSQL)

## Installatie

```bash
cd Source/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Database initialiseren

```bash
cp .env.example .env
docker compose up -d
./scripts/init_postgres.sh
```

Configuratie voor API (`APP_NAME`, `APP_VERSION`, `API_PREFIX`, `CORS_ALLOWED_ORIGINS`) en database (`PG*`) wordt automatisch uit `.env` geladen.

`init_postgres.sh` importeert daarna automatisch statische referentiedata uit `localfiles/output`:

- studenten: `students_import_normalized_v2.csv`
- reguliere producten: `products_regular_import_normalized.csv`
- verrassingsopdrachten: `products_surprise_import_normalized_v2.csv`
- beoordelaars: `assessors_import_normalized_v2.csv`

Import overslaan:

```bash
IMPORT_STATIC_DATA=false ./scripts/init_postgres.sh
```

Alleen statische data opnieuw importeren:

```bash
./scripts/import_static_data.sh
```

## Backend starten

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Alternatief:

```bash
source .venv/bin/activate
python run.py
```

Gebruik niet `python app/main.py`, omdat Python dat als los script uitvoert en package-imports zoals `from app...` dan niet kan resolven.

## Endpoints

Healthcheck:

```bash
curl http://127.0.0.1:8000/health
```

Create exam planning:

```bash
curl -X POST http://127.0.0.1:8000/api/exam-planning \
  -H "Content-Type: application/json" \
  -d '{
    "exam_date": "2026-06-10",
    "exam_type": "practical",
    "room": "B101",
    "exam_time": "09:00:00",
    "status": "planned"
  }'
```

List exam planning:

```bash
curl "http://127.0.0.1:8000/api/exam-planning?limit=50&offset=0"
```

Example exam for a quick database smoke test:

```bash
curl -X POST http://127.0.0.1:8000/api/exam-planning/example
```
