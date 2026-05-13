import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Exam Tool API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    cors_allowed_origins_raw: str = os.getenv("CORS_ALLOWED_ORIGINS", "*")

    pg_host: str = os.getenv("PGHOST", "localhost")
    pg_port: int = int(os.getenv("PGPORT", "5432"))
    pg_user: str = os.getenv("PGUSER", "exam_admin")
    pg_password: str = os.getenv("PGPASSWORD", "exam_admin")
    pg_database: str = os.getenv("PGDATABASE", "exam_tool")

    database_url: str = os.getenv("DATABASE_URL", "")

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url

        user = quote_plus(self.pg_user)
        password = quote_plus(self.pg_password)
        host = self.pg_host
        database = quote_plus(self.pg_database)
        return f"postgresql+psycopg://{user}:{password}@{host}:{self.pg_port}/{database}"

    @property
    def cors_allowed_origins(self) -> list[str]:
        if self.cors_allowed_origins_raw.strip() == "*":
            return ["*"]

        origins = [item.strip() for item in self.cors_allowed_origins_raw.split(",")]
        return [origin for origin in origins if origin] or ["*"]


settings = Settings()
