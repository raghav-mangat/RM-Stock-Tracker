from flask import render_template, current_app
from flask_mail import Message

def send_email(subject, recipients, text_body, html_body):
    mail = current_app.extensions.get("mail")
    msg = Message(
        subject=subject,
        recipients=recipients
    )
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        subject="[RM Stock Tracker] Reset Your Password",
        recipients=[user.email],
        text_body=render_template(
            "email/reset_password.txt",
            user=user,
            token=token
        ),
        html_body=render_template(
            "email/reset_password.html",
            user=user,
            token=token
        )
    )