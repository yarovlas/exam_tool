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

    mail_from: str = os.getenv("MAIL_FROM", "noreply@example.com")
    mail_from_name: str = os.getenv("MAIL_FROM_NAME", "Exam Tool")
    mailtrap_smtp_host: str = os.getenv("MAILTRAP_SMTP_HOST", "sandbox.smtp.mailtrap.io")
    mailtrap_smtp_port: int = int(os.getenv("MAILTRAP_SMTP_PORT", "2525"))
    mailtrap_smtp_username: str = os.getenv("MAILTRAP_SMTP_USERNAME", "")
    mailtrap_smtp_password: str = os.getenv("MAILTRAP_SMTP_PASSWORD", "")
    mailtrap_use_starttls: bool = os.getenv("MAILTRAP_USE_STARTTLS", "true").lower() in {
        "1",
        "true",
        "yes",
    }
    mailtrap_timeout_seconds: int = int(os.getenv("MAILTRAP_TIMEOUT_SECONDS", "10"))

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
