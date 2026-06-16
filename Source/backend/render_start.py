import os
import sys
from pathlib import Path


def main():
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        os.environ["DATABASE_URL"] = db_url.replace("postgres://", "postgresql+psycopg://", 1)

    backend_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(backend_dir))

    from sqlalchemy import text

    migrate_only = "--migrate-only" in sys.argv

    migrations_dir = backend_dir / "db" / "migrations"
    if not migrations_dir.is_dir():
        print(f"Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        session.execute(text(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(filename TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
        ))
        session.commit()

        result = session.execute(text("SELECT filename FROM schema_migrations"))
        applied = {row[0] for row in result}

        migration_files = sorted(migrations_dir.glob("*.sql"))

        for m_file in migration_files:
            name = m_file.name
            if name in applied:
                print(f"  Skipping {name} (already applied)")
                continue
            print(f"  Applying {name}...")
            sql = m_file.read_text()
            session.execute(text(sql))
            session.execute(
                text("INSERT INTO schema_migrations (filename) VALUES (:name) ON CONFLICT (filename) DO NOTHING"),
                {"name": name},
            )
            session.commit()
            print(f"  Applied {name}.")

        print("Migrations complete.")
    finally:
        session.close()

    if migrate_only:
        print("Pre-deploy migrations finished.")
        return

    port = os.environ.get("PORT", "8000")
    os.execvp("gunicorn", [
        "gunicorn",
        "-w", "2",
        "-k", "uvicorn.workers.UvicornWorker",
        "app.main:app",
        "--bind", f"0.0.0.0:{port}",
        "--access-logfile", "-",
        "--error-logfile", "-",
    ])


if __name__ == "__main__":
    main()
