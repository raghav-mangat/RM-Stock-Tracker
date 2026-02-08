from flask import current_app
from flask_mail import Message
from .base import EmailProvider

class SMTPEmailProvider(EmailProvider):
    def send(
        self,
        subject,
        recipients,
        text_body,
        html_body,
        inline_images=None,
    ):
        mail = current_app.extensions["mail"]

        msg = Message(
            subject=subject,
            recipients=recipients,
            body=text_body,
            html=html_body,
        )

        mail.send(msg)


"""
---------------------------------------------------------------------------------
- Code to attach inline images to the email
- Right now using image url from the server's static files instead
---------------------------------------------------------------------------------
"""
# from pathlib import Path
# def attach_images(images):
#     for cid, path in images.items():
#         with current_app.open_resource(path) as f:
#             msg.attach(
#                 filename=Path(path).name,
#                 content_type="image/png",
#                 data=f.read(),
#                 disposition="inline",
#                 headers={"Content-ID": f"<{cid}>"},
#             )
#
# default_images = {
#     "logo": "static/assets/email_icons/logo.png",
#     "instagram": "static/assets/email_icons/instagram.png",
#     "github": "static/assets/email_icons/github.png",
# }
# attach_images(default_images)
#
# if inline_images:
#     attach_images(inline_images)