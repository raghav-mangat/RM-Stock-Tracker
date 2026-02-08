from flask import current_app
from .smtp import SMTPEmailProvider
from .mailgun import MailgunEmailProvider

def get_email_provider():
    provider_config = current_app.config.get("EMAIL_PROVIDER", "smtp")
    email_provider = SMTPEmailProvider()

    if provider_config == "mailgun":
        email_provider = MailgunEmailProvider()

    return email_provider