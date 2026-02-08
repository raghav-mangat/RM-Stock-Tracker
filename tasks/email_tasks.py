from app import get_app

def send_email_task(
    subject: str,
    recipients: list[str],
    text_body: str,
    html_body: str,
    inline_images: dict | None = None
):
    """
    RQ job: Sends an email inside a Flask app context.
    """
    app = get_app()

    with app.app_context():
        from utils.emails.providers.factory import get_email_provider

        provider = get_email_provider()

        provider.send(
            subject,
            recipients,
            text_body,
            html_body,
            inline_images,
        )