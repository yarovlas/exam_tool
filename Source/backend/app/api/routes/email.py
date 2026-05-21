from fastapi import APIRouter, HTTPException, status

from app.schemas.email import TestEmailRequest, TestEmailResponse
from app.services.email import (
    EmailConfigurationError,
    EmailDeliveryError,
    send_mailtrap_test_email,
)


router = APIRouter(prefix="/email", tags=["email"])


@router.post("/test", response_model=TestEmailResponse, status_code=status.HTTP_202_ACCEPTED)
def send_test_email(payload: TestEmailRequest) -> TestEmailResponse:
    try:
        send_mailtrap_test_email(
            to_email=payload.to_email,
            recipient_name=payload.recipient_name,
            subject=payload.subject,
        )
    except EmailConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return TestEmailResponse(
        sent=True,
        message="Test email accepted by Mailtrap SMTP.",
        to_email=payload.to_email,
    )
