import requests
from flask import current_app
from .base import EmailProvider

class MailgunEmailProvider(EmailProvider):
    def send(
        self,
        subject,
        recipients,
        text_body,
        html_body,
        inline_images=None,
    ):
        config = current_app.config

        api_key = config["MAILGUN_API_KEY"]
        base = config["MAILGUN_BASE_URL"]
        version = config["MAILGUN_VERSION"]
        domain = config["MAILGUN_DOMAIN"]
        endpoint = config["MAILGUN_ENDPOINT"]
        sender = config["MAILGUN_DEFAULT_SENDER"]

        response = requests.post(
            f"{base}/{version}/{domain}/{endpoint}",
            auth=("api", api_key),
            data={
                "from": sender,
                "to": recipients,
                "subject": subject,
                "text": text_body,
                "html": html_body,
            },
            timeout=10,
        )

        response.raise_for_status()