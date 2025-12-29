from rq import Retry

class EmailService:

    @staticmethod
    def enqueue_auth_email(
        subject: str,
        recipients: list[str],
        text_body: str,
        html_body: str,
        inline_images: dict[str, str] | None = None
    ):
        """
        Enqueue auth email sending in Redis (non-blocking).
        """
        from tasks.email_tasks import send_email_task
        from app import email_high_queue

        email_high_queue.enqueue(
            send_email_task,
            subject,
            recipients,
            text_body,
            html_body,
            inline_images,
            job_timeout=120,
            retry=Retry(max=3, interval=[10, 30, 60]),
        )

    @staticmethod
    def enqueue_watchlist_email(
        subject: str,
        recipients: list[str],
        text_body: str,
        html_body: str,
        inline_images: dict[str, str] | None = None
    ):
        """
        Enqueue watchlist email sending in Redis (non-blocking).
        """
        from tasks.email_tasks import send_email_task
        from app import email_low_queue

        email_low_queue.enqueue(
            send_email_task,
            subject,
            recipients,
            text_body,
            html_body,
            inline_images,
            job_timeout=300,
            retry=Retry(max=2, interval=[60, 300]),
        )

    @staticmethod
    def send_email(
        subject: str,
        recipients: list[str],
        text_body: str,
        html_body: str,
        inline_images: dict[str, str] | None = None
    ):
        from flask import current_app
        from flask_mail import Message
        from pathlib import Path

        def add_inline_images(images):
            for cid, image_path in images.items():
                with current_app.open_resource(image_path) as f:
                    msg.attach(
                        filename=Path(image_path).name,
                        content_type="image/png",
                        data=f.read(),
                        disposition="inline",
                        headers={"Content-ID": f"<{cid}>"}
                    )

        mail = current_app.extensions["mail"]

        msg = Message(
            subject=subject,
            recipients=recipients,
            body=text_body,
            html=html_body
        )

        default_inline_images = {
            "logo": "static/assets/email_icons/logo.png",
            "instagram": "static/assets/email_icons/instagram.png",
            "github": "static/assets/email_icons/github.png"
        }
        add_inline_images(default_inline_images)

        if inline_images:
            add_inline_images(inline_images)

        mail.send(msg)
