# Backend (FastAPI + PostgreSQL)

Deze backend dekt stories #150-#153:

- #150: FastAPI backend start op PostgreSQL
- #151: backend-structuur met databaseconfiguratie
- #152: healthcheck endpoint + startup validatie
- #153: eerste API voor `exam_planning` (create + list)

## Structuur

- `app/main.py` - FastAPI app + startup DB check
- `app/core/config.py` - env-configuratie
- `app/db/session.py` - SQLAlchemy engine/session
- `app/api/routes/health.py` - `GET /health`
- `app/api/routes/exam_planning.py` -
  - `POST /api/exam-planning`
  - `GET /api/exam-planning`

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
