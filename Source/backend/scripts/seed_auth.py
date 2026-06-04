import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.auth import hash_password
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.auth import AppAuth


def main():
    email = settings.auth_email
    password = settings.auth_password

    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
    elif "--email" in sys.argv and "--password" in sys.argv:
        email = sys.argv[sys.argv.index("--email") + 1]
        password = sys.argv[sys.argv.index("--password") + 1]
    elif "--password" in sys.argv:
        password = sys.argv[sys.argv.index("--password") + 1]

    if not email or not password:
        print("Usage: python scripts/seed_auth.py [<email> <password>]")
        print("   or: python scripts/seed_auth.py --email admin@talland.nl --password admin123")
        print("   or: set AUTH_EMAIL + AUTH_PASSWORD in .env and run without args")
        sys.exit(1)

    password_hash = hash_password(password)

    db = SessionLocal()
    try:
        existing = db.execute(
            select(AppAuth).where(AppAuth.email == email)
        ).scalar_one_or_none()

        if existing:
            existing.password_hash = password_hash
            print(f"Updated credential for {email}")
        else:
            db.add(AppAuth(email=email, password_hash=password_hash))
            print(f"Created credential for {email}")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
