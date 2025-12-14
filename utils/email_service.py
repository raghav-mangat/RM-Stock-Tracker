from flask import current_app
from flask_mail import Message
from pathlib import Path

class EmailService:
    @staticmethod
    def send_email(
        subject: str,
        recipients: list[str],
        text_body: str,
        html_body: str,
        inline_images: dict[str, str] | None = None
    ):
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
