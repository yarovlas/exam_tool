from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from smtplib import SMTP, SMTPException
from string import Template

from app.core.config import BASE_DIR, settings


TEMPLATE_DIR = BASE_DIR / "app" / "templates" / "email"


class EmailConfigurationError(RuntimeError):
    pass


class EmailDeliveryError(RuntimeError):
    pass


def render_template(template_name: str, context: dict[str, str]) -> str:
    template_path = TEMPLATE_DIR / template_name
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.safe_substitute(context)


def send_mailtrap_test_email(to_email: str, recipient_name: str, subject: str) -> None:
    if not settings.mailtrap_smtp_username or not settings.mailtrap_smtp_password:
        raise EmailConfigurationError(
            "Mailtrap SMTP credentials are missing. Set MAILTRAP_SMTP_USERNAME and MAILTRAP_SMTP_PASSWORD."
        )

    context = {
        "recipient_name": recipient_name,
        "app_name": settings.app_name,
        "app_version": settings.app_version,
    }

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.mail_from_name, settings.mail_from))
    message["To"] = to_email
    message.set_content(render_template("mailtrap_test.txt", context))
    message.add_alternative(render_template("mailtrap_test.html", context), subtype="html")

    try:
        with SMTP(
            settings.mailtrap_smtp_host,
            settings.mailtrap_smtp_port,
            timeout=settings.mailtrap_timeout_seconds,
        ) as smtp:
            if settings.mailtrap_use_starttls:
                smtp.starttls()
            smtp.login(settings.mailtrap_smtp_username, settings.mailtrap_smtp_password)
            smtp.send_message(message)
    except (OSError, SMTPException) as exc:
        raise EmailDeliveryError("Mailtrap could not deliver the test email.") from exc
