from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.auth import hash_password
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.auth import AppAuth


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_db_status = "unknown"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        app.state.startup_db_status = "reachable"

        # Seed app_auth from env vars if table is empty
        if settings.auth_email and settings.auth_password:
            has_any = db.scalar(
                select(select(AppAuth.id).limit(1).exists())
            )
            if not has_any:
                db.add(AppAuth(
                    email=settings.auth_email,
                    password_hash=hash_password(settings.auth_password),
                ))
                db.commit()
    except SQLAlchemyError:
        app.state.startup_db_status = "unreachable"

    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "startup_db_status": app.state.startup_db_status,
    }
