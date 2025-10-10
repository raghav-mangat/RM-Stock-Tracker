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
    expires_in = 1800 # 30 minutes
    token = user.get_token(token_type="reset_password", expires_in=expires_in)
    send_email(
        subject="Reset Your Password - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/reset_password.txt",
            user=user,
            token=token
        ),
        html_body=render_template(
            "email/reset_password.html",
            user=user,
            token=token,
            expires_in=expires_in
        )
    )

def send_verify_user_email(user):
    token = user.get_token(token_type="verify_email")
    send_email(
        subject="Verify Your Email - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/verify_email.txt",
            user=user,
            token=token
        ),
        html_body=render_template(
            "email/verify_email.html",
            user=user,
            token=token
        )
    )

def send_password_reset_success_email(user):
    send_email(
        subject="Your Password Has Been Changed - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/password_reset_success.txt",
            user=user,
        ),
        html_body=render_template(
            "email/password_reset_success.html",
            user=user,
        )
    )

def send_user_verification_success_email(user):
    send_email(
        subject="Your Email Has Been Verified - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/user_verification_success.txt",
            user=user,
        ),
        html_body=render_template(
            "email/user_verification_success.html",
            user=user,
        )
    )