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
        from utils.email_service import EmailService

        EmailService.send_email(
            subject=subject,
            recipients=recipients,
            text_body=text_body,
            html_body=html_body,
            inline_images=inline_images,
        )