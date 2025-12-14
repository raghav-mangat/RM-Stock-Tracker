from flask import render_template
from utils.email_service import EmailService

class AuthEmail(EmailService):

    @classmethod
    def verify_email(cls, user):
        token = user.get_token(token_type="verify_email")
        cls.send_email(
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

    @classmethod
    def reset_password(cls, user):
        expires_in = 1800 # 30 minutes
        token = user.get_token(token_type="reset_password", expires_in=expires_in)
        cls.send_email(
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

    @classmethod
    def settings_reset_password(cls, user):
        expires_in = 1800 # 30 minutes
        token = user.get_token(token_type="settings_reset_password", expires_in=expires_in)
        cls.send_email(
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

    @classmethod
    def delete_account(cls, user):
        expires_in = 1200 # 20 minutes
        token = user.get_token(token_type="delete_account", expires_in=expires_in)
        cls.send_email(
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

    @classmethod
    def user_verification_success(cls, user):
        cls.send_email(
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

    @classmethod
    def google_signin_success(cls, user):
        cls.send_email(
            subject="You have Signed In With Google - RM Stock Tracker",
            recipients=[user.email],
            text_body=render_template(
                "email/google_signin_success.txt",
                user=user,
            ),
            html_body=render_template(
                "email/google_signin_success.html",
                user=user,
            )
        )

    @classmethod
    def settings_password_set_success(cls, user):
        cls.send_email(
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

    @classmethod
    def settings_password_removed_success(cls, user):
        cls.send_email(
            subject="Password Removed from Your Account - RM Stock Tracker",
            recipients=[user.email],
            text_body=render_template(
                "email/settings_password_removed_success.txt",
                user=user,
            ),
            html_body=render_template(
                "email/settings_password_removed_success.html",
                user=user,
            )
        )

    @classmethod
    def google_account_linked_success(cls, user):
        cls.send_email(
            subject="Google Account Linked Successfully - RM Stock Tracker",
            recipients=[user.email],
            text_body=render_template(
                "email/google_account_linked_success.txt",
                user=user,
            ),
            html_body=render_template(
                "email/google_account_linked_success.html",
                user=user,
            )
        )

    @classmethod
    def google_account_unlinked_success(cls, user):
        cls.send_email(
            subject="Google Account Unlinked - RM Stock Tracker",
            recipients=[user.email],
            text_body=render_template(
                "email/google_account_unlinked_success.txt",
                user=user,
            ),
            html_body=render_template(
                "email/google_account_unlinked_success.html",
                user=user,
            )
        )

    @classmethod
    def password_reset_success(cls, user):
        cls.send_email(
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

    @classmethod
    def account_delete_success(cls, user):
        cls.send_email(
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