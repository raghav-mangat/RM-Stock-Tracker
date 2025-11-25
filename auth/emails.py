from flask import render_template, current_app
from flask_mail import Message
from pathlib import Path

def send_email(subject, recipients, text_body, html_body):
    mail = current_app.extensions.get("mail")
    msg = Message(
        subject=subject,
        recipients=recipients
    )
    msg.body = text_body
    msg.html = html_body

    # Attach inline images
    images={
        "logo": "static/assets/email_icons/logo.png",
        "instagram": "static/assets/email_icons/instagram.png",
        "github": "static/assets/email_icons/github.png"
    }
    for cid, image_path in images.items():
        with current_app.open_resource(image_path) as f:
            msg.attach(
                filename=Path(image_path).name,
                content_type="image/png",
                data=f.read(),
                disposition="inline",
                headers={'Content-ID': f'<{cid}>'}
            )

    mail.send(msg)

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

def send_password_reset_email(user):
    expires_in = 1800 # 30 minutes
    token = user.get_token(token_type="reset_password", expires_in=expires_in)
    send_email(
        subject="Reset Your Password - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/reset_password.txt",
            user=user,
            token=token,
            expires_in=expires_in
        ),
        html_body=render_template(
            "email/reset_password.html",
            user=user,
            token=token,
            expires_in=expires_in
        )
    )

def send_settings_password_reset_email(user):
    expires_in = 1800 # 30 minutes
    token = user.get_token(token_type="settings_reset_password", expires_in=expires_in)
    send_email(
        subject="Reset Your Password - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/settings_reset_password.txt",
            user=user,
            token=token,
            expires_in=expires_in
        ),
        html_body=render_template(
            "email/settings_reset_password.html",
            user=user,
            token=token,
            expires_in=expires_in
        )
    )

def send_delete_account_email(user):
    expires_in = 1200 # 20 minutes
    token = user.get_token(token_type="delete_account", expires_in=expires_in)
    send_email(
        subject="Delete Your Account - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/delete_account.txt",
            user=user,
            token=token,
            expires_in=expires_in
        ),
        html_body=render_template(
            "email/delete_account.html",
            user=user,
            token=token,
            expires_in=expires_in
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

def send_login_google_success_email(user):
    send_email(
        subject="You have Logged In With Google - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/login_google_success.txt",
            user=user,
        ),
        html_body=render_template(
            "email/login_google_success.html",
            user=user,
        )
    )

def send_settings_password_set_success_email(user):
    send_email(
        subject="Password Created for Your Account - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/settings_password_set_success.txt",
            user=user,
        ),
        html_body=render_template(
            "email/settings_password_set_success.html",
            user=user,
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

def send_account_delete_success_email(user):
    send_email(
        subject="Your Account Has Been Deleted - RM Stock Tracker",
        recipients=[user.email],
        text_body=render_template(
            "email/account_delete_success.txt",
            user=user,
        ),
        html_body=render_template(
            "email/account_delete_success.html",
            user=user,
        )
    )