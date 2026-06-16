from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_current_user, hash_password, verify_password
from app.db.session import get_db
from app.models.auth import AppAuth
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse, PasswordChangeRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    credential = db.execute(
        select(AppAuth).where(AppAuth.email == payload.email)
    ).scalar_one_or_none()

    if credential is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ongeldige gegevens")

    if not verify_password(payload.password, credential.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ongeldige gegevens")

    token = create_access_token(payload.email)
    return LoginResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(email: str = Depends(get_current_user)):
    return MeResponse(email=email)


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChangeRequest,
    email: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    credential = db.execute(
        select(AppAuth).where(AppAuth.email == email)
    ).scalar_one_or_none()

    if credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gebruiker niet gevonden")

    if not verify_password(payload.current_password, credential.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Huidig wachtwoord onjuist")

    credential.password_hash = hash_password(payload.new_password)
    db.commit()
