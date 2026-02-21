from . import auth_bp
from flask import (
    render_template, redirect, url_for, flash, session, request,
    current_app, get_flashed_messages
)
from flask_login import current_user, login_user, login_required
from authlib.integrations.flask_client import OAuthError
import secrets
import time
from extensions import limiter
from models.database import User, SignupSource
from metrics import metrics
from metrics.registry import MetricName
from .emails import AuthEmail
from .services import RedirectService, LogoutService
from .forms import (
    LoginForm, SignupForm, ChooseUsernameForm, ResetPasswordRequestForm, ResetPasswordForm, ProfileSettingsForm,
    SettingsDeleteAccountRequestForm, DeleteAccountForm, SettingsResetPasswordRequestForm, SettingsUnlinkGoogleAccountForm,
    SettingsSetPasswordForm, SettingsRemovePasswordForm, SettingsToggleEmailAlertsForm
)
from utils.db_queries.user_data import (
    AuthError, AuthUnexpectedError, add_new_user, update_user_profile, change_user_password, verify_user,
    get_user_by_email, get_user_by_google_id, delete_user_account, add_user_google_id, remove_user_google_id,
    remove_user_password, update_user_last_login_at, toggle_user_email_alerts_on, is_user_verified
)
from utils.flask_rate_limits import ip_and_email
from utils.emails.email_rate_limiter import EmailType


@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit(
    "10 per minute; 50 per hour; 250 per day",
    key_func=ip_and_email,
    methods=["POST"]
)
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))

    form = SignupForm()

    if form.validate_on_submit():
        try:
            user = add_new_user(
                signup_source=SignupSource.EMAIL,
                email=form.email.data,
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                password=form.password.data,
                google_id=None,
                is_verified=False
            )

            current_app.logger.info(
                "New user joined with email",
                extra={"log_type": "auth", "user_id": user.id, "email": user.email}
            )

            try:
                AuthEmail.verify_email(user)
                flash(
                    "Account created, we sent a verification email. Please click the link in your inbox (check spam).",
                    "success")
            except Exception:
                current_app.logger.exception(
                    "Failed to send account verification email",
                    extra={"log_type": "auth", "user_id": user.id}
                )
                flash(
                    "Account created, but we couldn't send the verification email. "
                    "You can resend it after logging in.",
                    "warning"
                )

            return redirect(url_for('auth.login'))

        except AuthUnexpectedError as e:
            current_app.logger.exception(
                "Unexpected error during user signup with email",
                extra={"log_type": "auth", "email": form.email.data}
            )
            flash(str(e), "danger")
            return redirect(url_for("auth.signup"))
        except AuthError as e:
            flash(str(e), "danger")
            return redirect(url_for('auth.signup'))

    return render_template("signup.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit(
    "10 per minute; 50 per hour; 250 per day",
    key_func=ip_and_email,
    methods=["POST"]
)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)

        if not user.is_verified:
            try:
                email_sent, ttl = AuthEmail.send_rate_limited_email(
                    user=user,
                    email_func=AuthEmail.verify_email,
                    email_type=EmailType.VERIFY_EMAIL
                )
            except Exception:
                current_app.logger.exception(
                    "Failed to send account verification email",
                    extra={"log_type": "auth", "user_id": user.id}
                )
                flash(
                    "Account not verified. We couldn't resend the verification email right now. "
                    "Please try again later.",
                    "warning"
                )
                return redirect(url_for('auth.login'))

            if email_sent:
                flash(
                    "Account not verified. We sent a verification email. Please check your inbox (and spam).",
                    "warning"
                )
            else:
                current_app.logger.warning(
                    "Email rate limit exceeded for account verification",
                    extra={"log_type": "auth", "user_id": user.id}
                )
                flash(
                    f"Account not verified. Please check your inbox (and spam) for a verification email. You can request another email in {ttl} seconds by logging in.",
                    "warning"
                )

            return redirect(url_for('auth.login'))

        login_user(user)
        update_user_last_login_at(user)
        session["security_timestamp"] = user.security_timestamp

        current_app.logger.info(
            "User logged in with email",
            extra={"log_type": "auth", "user_id": user.id}
        )

        flash("Logged in successfully!", "success")

        return redirect(RedirectService.get_post_login_redirect())

    return render_template("login.html", form=form)

@auth_bp.route("/logout", methods=["GET"])
@login_required
def logout():
    LogoutService.perform_logout()

    if not get_flashed_messages(with_categories=True):
        flash("Logged out successfully", "success")

    return redirect(url_for('home'))

@auth_bp.route("/settings")
@login_required
def settings():
    return redirect(url_for("auth.settings_profile"))

@auth_bp.route("/settings/profile", methods=["GET", "POST"])
@login_required
def settings_profile():
    profile_settings_form = ProfileSettingsForm(obj=current_user)

    if profile_settings_form.validate_on_submit():
        try:
            update_user_profile(
                user=current_user,
                first_name=profile_settings_form.first_name.data,
                last_name=profile_settings_form.last_name.data,
                username=profile_settings_form.username.data
            )

            current_app.logger.info(
                "Profile settings updated",
                extra={"log_type": "auth"}
            )

            flash("Profile updated successfully.", "success")

        except AuthUnexpectedError as e:
            current_app.logger.exception(
                "Unexpected error during profile settings update",
                extra={"log_type": "auth"}
            )
            flash(str(e), "danger")
        except AuthError as e:
            flash(str(e), "danger")

        return redirect(url_for("auth.settings_profile"))

    elif request.method == "POST":
        flash(
            "Could not update your profile. Please review the highlighted fields and try again.",
            "warning"
        )

    return render_template(
        "settings/profile.html",
        active_tab="profile",
        profile_settings_form=profile_settings_form,
    )

@auth_bp.route("/settings/account", methods=["GET"])
@login_required
def settings_account():
    return render_template(
        "settings/account.html",
        active_tab="account",
        settings_toggle_email_alerts_form=SettingsToggleEmailAlertsForm(),
        settings_unlink_google_account_form=SettingsUnlinkGoogleAccountForm(),
        settings_reset_password_request_form=SettingsResetPasswordRequestForm(),
        settings_remove_password_form=SettingsRemovePasswordForm(),
        settings_delete_account_request_form=SettingsDeleteAccountRequestForm(),
    )

@auth_bp.route("/verify-email/<string:token>", methods=["GET"])
def verify_email(token):
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))

    user = User.verify_token(token, token_type="verify_email")
    if not user:
        flash("The verification link is invalid or has expired. Please request a new verification email by logging in.", "danger")
        return redirect(url_for("auth.login"))

    if user.is_verified:
        flash("Your email is already verified. Please log in.", "info")
        return redirect(url_for("auth.login"))

    try:
        verify_user(user)

        current_app.logger.info(
            "Email verification completed",
            extra={"log_type": "auth", "user_id": user.id}
        )

        flash("Your email is verified! Now you can log in.", "success")

        try:
            AuthEmail.user_verification_success(user)
        except Exception:
            current_app.logger.exception(
                "Failed to send account verification success email",
                extra={"log_type": "auth", "user_id": user.id}
            )

    except AuthUnexpectedError as e:
        current_app.logger.exception(
            "Unexpected error during email verification",
            extra={"log_type": "auth", "user_id": user.id}
        )
        flash(str(e), "danger")
    except AuthError as e:
        flash(str(e), "danger")

    return redirect(url_for("auth.login"))

@auth_bp.route("/reset-password-request", methods=["GET", "POST"])
@limiter.limit(
    "3 per minute; 10 per hour; 25 per day",
    key_func=ip_and_email,
    methods=["POST"]
)
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)

        if not user:
            flash("No account found with that email.", "warning")
            return redirect(url_for("auth.login"))

        try:
            email_sent, ttl = AuthEmail.send_rate_limited_email(
                user=user,
                email_func=AuthEmail.reset_password,
                email_type=EmailType.RESET_PASSWORD
            )
        except Exception:
            current_app.logger.exception(
                "Failed to send password reset email",
                extra={"log_type": "auth", "user_id": user.id}
            )
            flash("Could not send password reset email. Please try again later.", "danger")
            return redirect(url_for("auth.login"))

        if email_sent:
            current_app.logger.info(
                "Password reset email sent",
                extra={"log_type": "auth", "user_id": user.id}
            )
            flash("Check your inbox (and spam) for an email containing password reset instructions.", "success")
        else:
            current_app.logger.warning(
                "Email rate limit exceeded for reset password request",
                extra={"log_type": "auth", "user_id": user.id}
            )
            flash(f"Please wait {ttl} seconds before requesting another password reset email.", "warning")

        return redirect(url_for("auth.login"))

    return render_template("reset_password_request.html", form=form)

@auth_bp.route("/settings-toggle-email-alerts", methods=["POST"])
@login_required
def settings_toggle_email_alerts():
    form = SettingsToggleEmailAlertsForm()

    if form.validate_on_submit():
        try:
            toggle_user_email_alerts_on(current_user)
            if current_user.email_alerts_on:
                current_app.logger.info(
                    "Email alerts turned on",
                    extra={"log_type": "auth"}
                )

                flash("Email alerts have been turned ON.", "success")
            else:
                current_app.logger.info(
                    "Email alerts turned off",
                    extra={"log_type": "auth"}
                )

                flash("Email alerts have been turned OFF.","success")
        except AuthUnexpectedError as e:
            current_app.logger.exception(
                "Unexpected error during email alerts toggle",
                extra={"log_type": "auth"}
            )
            flash(str(e), "danger")
        except AuthError as e:
            flash(str(e), "danger")
    else:
        flash("Invalid request.", "danger")

    return redirect(url_for("auth.settings_account"))

@auth_bp.route("/settings/set-password", methods=["GET", "POST"])
@login_required
def settings_set_password():
    # Only for users who do not already have a password
    if current_user.password_hash:
        flash("You already have a password. Use Reset Password instead.", "warning")
        return redirect(url_for("auth.settings_account"))

    reauth_verified = session.get("reauth_verified")
    reauth_time = session.get("reauth_verified_at", 0)

    # Check expiry (5 minutes or 300 seconds)
    reauth_duration = 300
    reauth_expired = not reauth_verified or (time.time() - reauth_time > reauth_duration)

    form = SettingsSetPasswordForm()

    if request.method == "POST":
        if reauth_expired:
            flash("Your Google sign-in verification expired. Please try again.", "warning")
            return redirect(url_for("auth.settings_account"))
        if form.validate_on_submit():
            # Consume reauth proof
            session.pop("reauth_verified", None)
            session.pop("reauth_verified_at", None)

            try:
                change_user_password(current_user, form.password.data)

                current_app.logger.info(
                    "Password set",
                    extra={"log_type": "auth"}
                )

                flash("Your password has been set. Please log in again.", "success")

                try:
                    AuthEmail.settings_password_set_success(current_user)
                except Exception:
                    current_app.logger.exception(
                        "Failed to send password set success email",
                        extra={"log_type": "auth"}
                    )

            except AuthUnexpectedError as e:
                current_app.logger.exception(
                    "Unexpected error during password set",
                    extra={"log_type": "auth"}
                )
                flash(str(e), "danger")
            except AuthError as e:
                flash(str(e), "danger")

            return redirect(url_for("auth.logout"))

    if reauth_expired:
        session["reauth_next"] = url_for(
            "auth.settings_set_password", _external=True
        )
        return redirect(url_for("auth.google_reauth"))
    else:
        flash(
            "Your Google sign-in was recently verified. You can now set your password.",
            "info"
        )

    return render_template("settings_set_password.html", form=form)

@auth_bp.route("/settings-reset-password-request", methods=["POST"])
@login_required
def settings_reset_password_request():
    form = SettingsResetPasswordRequestForm()

    if not form.validate_on_submit():
        return redirect(url_for("auth.settings_account"))

    try:
        email_sent, ttl = AuthEmail.send_rate_limited_email(
            user=current_user,
            email_func=AuthEmail.settings_reset_password,
            email_type=EmailType.SETTINGS_RESET_PASSWORD
        )
    except Exception:
        current_app.logger.exception(
            "Failed to send password reset email from settings",
            extra={"log_type": "auth"}
        )
        flash("Could not send password reset email. Please try again later.", "danger")
        return redirect(url_for("auth.settings_account"))

    if email_sent:
        current_app.logger.info(
            "Password reset email sent from settings",
            extra={"log_type": "auth"}
        )

        flash("Check your email for the instructions to reset your password.", "success")
    else:
        current_app.logger.warning(
            "Email rate limit exceeded for settings reset password request",
            extra={"log_type": "auth"}
        )

        flash(f"Please wait {ttl} seconds before requesting another password reset email.", "warning")

    return redirect(url_for("auth.settings_account"))

@auth_bp.route("/settings-remove-password", methods=["POST"])
@login_required
def settings_remove_password():
    form = SettingsRemovePasswordForm()

    if not current_user.password_hash:
        flash("You must set a password before removing your password.", "danger")
    elif not current_user.google_id:
        flash("You must link your Google account before removing your password.", "warning")
    elif not form.validate_on_submit():
        flash("Please enter your password.", "warning")
    elif not current_user.verify_password(form.remove_password.data):
        flash("Incorrect password.", "warning")
    else:
        try:
            remove_user_password(current_user)

            current_app.logger.info(
                "Password removed",
                extra={"log_type": "auth"}
            )

            flash("Your password has been removed. Please log in again.", "success")

            try:
                AuthEmail.settings_password_removed_success(current_user)
            except Exception:
                current_app.logger.exception(
                    "Failed to send password removed success email",
                    extra={"log_type": "auth"}
                )

        except AuthUnexpectedError as e:
            current_app.logger.exception(
                "Unexpected error during password remove",
                extra={"log_type": "auth"}
            )
            flash(str(e), "danger")
        except AuthError as e:
            flash(str(e), "danger")
        return redirect(url_for("auth.logout"))
    return redirect(url_for("auth.settings_account"))

@auth_bp.route("/reset-password/<string:token>", methods=["GET", "POST"])
def reset_password(token):
    # Check both types
    for token_type in ("reset_password", "settings_reset_password"):
        user = User.verify_token(token, token_type=token_type)
        if user:
            break

    if not user:
        flash("The reset password link is invalid or has expired. Please request a new link to reset password.",
              "danger")
        return redirect(url_for("auth.login"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            change_user_password(user, form.password.data)

            current_app.logger.info(
                "Password reset",
                extra={"log_type": "auth", "user_id": user.id}
            )

            flash("Your password has been reset. Please log in.", "success")
            try:
                AuthEmail.password_reset_success(user)
            except Exception:
                current_app.logger.exception(
                    "Failed to send password reset success email",
                    extra={"log_type": "auth", "user_id": user.id}
                )
                pass

        except AuthUnexpectedError as e:
            current_app.logger.exception(
                "Unexpected error during password reset",
                extra={"log_type": "auth", "user_id": user.id}
            )
            flash(str(e), "danger")
        except AuthError as e:
            flash(str(e), "danger")

        if current_user.is_authenticated:
            return redirect(url_for("auth.logout"))
        else:
            return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form)

@auth_bp.route("/delete-account-request", methods=["POST"])
@login_required
def delete_account_request():
    form = SettingsDeleteAccountRequestForm()

    # Check password only if the password exists
    if current_user.password_hash:
        # User must enter password
        if not form.validate_on_submit():
            flash("Please enter your password.", "warning")
            return redirect(url_for("auth.settings_account"))

        if not current_user.verify_password(form.delete_account_password.data):
            flash("Incorrect password.", "warning")
            return redirect(url_for("auth.settings_account"))

    try:
        email_sent, ttl = AuthEmail.send_rate_limited_email(
            user=current_user,
            email_func=AuthEmail.delete_account,
            email_type=EmailType.DELETE_ACCOUNT
        )
    except Exception:
        current_app.logger.exception(
            "Failed to send account deletion email",
            extra={"log_type": "auth"}
        )
        flash("Could not send account deletion email. Please try again later.", "warning")
        return redirect(url_for("auth.settings_account"))

    if email_sent:
        current_app.logger.info(
            "Account deletion email sent",
            extra={"log_type": "auth"}
        )

        flash("Check your email for the instructions to delete your account.", "success")
    else:
        current_app.logger.warning(
            "Email rate limit exceeded for delete account request",
            extra={"log_type": "auth"}
        )

        flash(f"Please wait {ttl} seconds before requesting another account deletion email.", "warning")

    return redirect(url_for("auth.settings_account"))

@auth_bp.route("/delete-account/<string:token>", methods=["GET", "POST"])
def delete_account(token):
    user = User.verify_token(token, token_type="delete_account")
    if not user:
        flash("The delete account link is invalid or has expired. Please request a new link to delete your account.",
              "danger")
        return redirect(url_for("auth.login"))

    form = DeleteAccountForm()
    if form.validate_on_submit():
        if user.email == form.email.data:
            user_id = user.id
            try:
                email = user.email

                delete_user_account(user)

                current_app.logger.info(
                    "User deleted their account",
                    extra={"log_type": "auth", "user_id": user_id, "email": email}
                )

                try:
                    AuthEmail.account_delete_success(user)
                except Exception:
                    current_app.logger.exception(
                        "Failed to send account deleted success email",
                        extra={"log_type": "auth", "user_id": user_id}
                    )

                flash("Your account has been deleted.", "success")

            except AuthUnexpectedError as e:
                current_app.logger.exception(
                    "Unexpected error during account deletion",
                    extra={"log_type": "auth", "user_id": user.id}
                )
                flash(str(e), "danger")
            except AuthError as e:
                flash(str(e), "danger")

            if current_user.is_authenticated and current_user.id == user_id:
                LogoutService.perform_logout()

            return redirect(url_for("auth.login"))
        else:
            flash("Incorrect email to delete account.", "warning")
            return redirect(url_for("auth.delete_account", token=token))
    return render_template("delete_account.html", form=form)

@auth_bp.route("/google/signin")
def google_signin():
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))

    oauth = current_app.config["OAUTH"]

    # Create state to protect against CSRF
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)

    session["oauth_state"] = state
    session["oauth_nonce"] = nonce

    # Persist next url
    next_url = request.args.get("next")
    if next_url and RedirectService.is_safe_redirect_url(next_url):
        session["oauth_next"] = next_url

    redirect_uri = url_for("auth.google_signin_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri, state=state, nonce=nonce)

@auth_bp.route("/google/signin/callback")
def google_signin_callback():
    metrics.increment(MetricName.GOOGLE_OAUTH_CALLBACKS)

    oauth = current_app.config["OAUTH"]

    # Check state
    state_in_session = session.pop("oauth_state", None)
    state_returned = request.args.get("state")
    if not state_in_session or not state_returned or state_in_session != state_returned:
        flash("Something went wrong during login. Please try again.", "danger")
        return redirect(url_for("auth.login"))

    try:
        # Exchanges code for tokens
        token = oauth.google.authorize_access_token()
    except OAuthError:
        flash("Authentication failed. Try again.", "danger")
        return redirect(url_for("auth.login"))

    # Parse and verify id_token (Authlib will validate the token)
    try:
        userinfo = oauth.google.parse_id_token(
            token,
            nonce=session.pop("oauth_nonce", None)
        )
    except Exception:
        flash("Failed to fetch account information from Google.", "danger")
        return redirect(url_for("auth.login"))

    # Extract important claims
    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified", False)
    first_name = userinfo.get("given_name") or ""
    last_name = userinfo.get("family_name") or ""

    if not email or not google_id:
        flash("Google did not return required information", "danger")
        return redirect(url_for("auth.login"))

    if not email_verified:
        flash("Please verify your Google email before signing in.", "warning")
        return redirect(url_for("auth.login"))

    user = get_user_by_email(email)
    if user:
        if user.google_id:
            if user.google_id != google_id:
                flash("This Google account is not linked to your profile.", "warning")
                return redirect(url_for("auth.login"))
            else:
                flash("Signed in with Google.", "success")
        else:
            existing = get_user_by_google_id(google_id)
            if existing:
                flash("This Google account is already linked to another user.", "danger")
                return redirect(url_for("auth.login"))
            else:
                try:
                    add_user_google_id(user, google_id)

                    current_app.logger.info(
                        "Google account auto-linked",
                        extra={"log_type": "auth", "user_id": user.id}
                    )

                    message = "Signed in with Google. Auto-Linked Google account successfully."

                    try:
                        AuthEmail.google_account_auto_linked_success(user)
                    except Exception:
                        current_app.logger.exception(
                            "Failed to send Google account auto-linked success email",
                            extra={"log_type": "auth", "user_id": user.id}
                        )

                    if not is_user_verified(user):
                        try:
                            verify_user(user)

                            current_app.logger.info(
                                "Email verification completed",
                                extra={"log_type": "auth", "user_id": user.id}
                            )

                            message += " Your email is verified."

                            try:
                                AuthEmail.user_verification_success(user)
                            except Exception:
                                current_app.logger.exception(
                                    "Failed to send account verification success email",
                                    extra={"log_type": "auth", "user_id": user.id}
                                )

                        except AuthUnexpectedError as e:
                            current_app.logger.exception(
                                "Unexpected error during email verification",
                                extra={"log_type": "auth", "user_id": user.id}
                            )
                            flash(str(e), "danger")
                        except AuthError as e:
                            flash(str(e), "danger")

                    flash(message, "success")

                except AuthUnexpectedError as e:
                    current_app.logger.exception(
                        "Unexpected error during Google signin auto-link",
                        extra={"log_type": "auth", "user_id": user.id}
                    )
                    flash(f"Unable to signin with Google. {str(e)}", "danger")
                    return redirect(url_for("auth.login"))
                except AuthError as e:
                    flash(f"Unable to signin with Google. {str(e)}", "danger")
                    return redirect(url_for("auth.login"))
    else:
        session["pending_google_signup"] = {
            "google_id": google_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "created_at": time.time()
        }
        return redirect(url_for("auth.choose_username"))

    login_user(user)
    update_user_last_login_at(user)
    session["security_timestamp"] = user.security_timestamp

    current_app.logger.info(
        "User logged in with Google",
        extra={"log_type": "auth", "user_id": user.id}
    )

    # Restore next url safely
    next_url = session.pop("oauth_next", None)
    if next_url and RedirectService.is_safe_redirect_url(next_url):
        return redirect(next_url)

    return redirect(url_for("watchlist.index"))

@auth_bp.route("/choose-username", methods=["GET", "POST"])
def choose_username():
    pending = session.get("pending_google_signup")

    # User tries to access manually or session expired
    if not pending:
        flash("Your sign-in session expired. Please continue by signing in with Google again.","warning")
        return redirect(url_for("auth.login"))

    # Prevent stale sessions
    stale_session_delta = 15 * 60 # 15 minutes
    if time.time() - pending["created_at"] > stale_session_delta:
        session.pop("pending_google_signup", None)
        flash("Signup session expired. Please sign in again.", "warning")
        return redirect(url_for("auth.login"))

    form = ChooseUsernameForm()

    if form.validate_on_submit():
        try:
            user = add_new_user(
                signup_source=SignupSource.GOOGLE,
                email=pending["email"],
                username=form.username.data,
                first_name=pending["first_name"],
                last_name=pending["last_name"],
                password=None,
                google_id=pending["google_id"],
                is_verified=True,
            )
            current_app.logger.info(
                "New user joined with Google",
                extra={"log_type": "auth", "user_id": user.id, "email": user.email}
            )

            session.pop("pending_google_signup", None)

            try:
                AuthEmail.google_signin_success(user)
            except Exception:
                current_app.logger.exception(
                    "Failed to send Google signin success email",
                    extra={"log_type": "auth", "user_id": user.id}
                )

            login_user(user)
            update_user_last_login_at(user)
            session["security_timestamp"] = user.security_timestamp

            current_app.logger.info(
                "User logged in with Google",
                extra={"log_type": "auth", "user_id": user.id}
            )

            flash("Signed in with Google. Account created successfully.", "success")

            # Restore next url safely
            next_url = session.pop("oauth_next", None)
            if next_url and RedirectService.is_safe_redirect_url(next_url):
                return redirect(next_url)

            return redirect(url_for("watchlist.index"))

        except AuthUnexpectedError as e:
            current_app.logger.exception(
                "Unexpected error during choosing username after user Google signup",
                extra={"log_type": "auth", "email": pending["email"]}
            )
            flash(str(e), "danger")
            return redirect(url_for("auth.choose_username"))
        except AuthError as e:
            flash(str(e), "danger")
            return redirect(url_for("auth.choose_username"))
        finally:
            # Clean up the session
            session.pop("pending_google_signup", None)
            session.pop("oauth_next", None)

    return render_template("choose_username.html", form=form)

@auth_bp.route("/google/link")
@login_required
def google_link():
    oauth = current_app.config["OAUTH"]

    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)

    session["link_state"] = state
    session["link_nonce"] = nonce

    redirect_uri = url_for("auth.google_link_callback", _external=True)

    return oauth.google.authorize_redirect(
        redirect_uri,
        state=state,
        nonce=nonce
    )

@auth_bp.route("/google/link/callback")
@login_required
def google_link_callback():
    metrics.increment(MetricName.GOOGLE_OAUTH_CALLBACKS)

    oauth = current_app.config["OAUTH"]

    state_in_session = session.pop("link_state", None)
    state_returned = request.args.get("state")
    if not state_in_session or not state_returned or state_in_session != state_returned:
        flash("Something went wrong while linking your Google account. Please try again.", "danger")
        return redirect(url_for("auth.settings_account"))

    try:
        # Exchanges code for tokens
        token = oauth.google.authorize_access_token()
    except OAuthError:
        flash("Authentication failed. Try again.", "danger")
        return redirect(url_for("auth.settings_account"))

    # Parse and verify id_token (Authlib will validate the token)
    try:
        userinfo = oauth.google.parse_id_token(
            token,
            nonce=session.pop("link_nonce", None)
        )
    except Exception:
        flash("Failed to fetch account information from Google.", "danger")
        return redirect(url_for("auth.settings_account"))

    # Extract important claims
    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified", False)

    if not email or not google_id:
        flash("Google did not return required information", "danger")
        return redirect(url_for("auth.settings_account"))

    # Emails must match
    if email != current_user.email:
        flash("The Google account email must match your account email.", "warning")
        return redirect(url_for("auth.settings_account"))

    # Email must be verified
    if not email_verified:
        flash("Please verify your Google email before linking your account.", "warning")
        return redirect(url_for("auth.settings_account"))

    existing = get_user_by_google_id(google_id)
    if existing and existing.id != current_user.id:
        flash("This Google account is already linked to another user.", "danger")
        return redirect(url_for("auth.settings_account"))

    try:
        add_user_google_id(current_user, google_id)

        current_app.logger.info(
            "Google account linked",
            extra={"log_type": "auth"}
        )

        flash("Google account linked successfully. Please log in again.", "success")

        try:
            AuthEmail.google_account_linked_success(current_user)
        except Exception:
            current_app.logger.exception(
                "Failed to send Google account linked success email",
                extra={"log_type": "auth"}
            )

    except AuthUnexpectedError as e:
        current_app.logger.exception(
            "Unexpected error during Google account linking",
            extra={"log_type": "auth"}
        )
        flash(str(e), "danger")
    except AuthError as e:
        flash(str(e), "danger")

    return redirect(url_for("auth.logout"))

@auth_bp.route("/google/unlink", methods=["POST"])
@login_required
def google_unlink():
    form = SettingsUnlinkGoogleAccountForm()

    if not current_user.password_hash:
        flash("You must set a password before unlinking your Google account.", "warning")
    elif not form.validate_on_submit():
        flash("Please enter your password.", "warning")
    elif not current_user.verify_password(form.unlink_google_password.data):
        flash("Incorrect password.", "warning")
    else:
        try:
            remove_user_google_id(current_user)

            current_app.logger.info(
                "Google account unlinked",
                extra={"log_type": "auth"}
            )

            flash("Your Google account has been unlinked. Please log in again.", "success")

            try:
                AuthEmail.google_account_unlinked_success(current_user)
            except Exception:
                current_app.logger.exception(
                    "Failed to send Google account unlink success email",
                    extra={"log_type": "auth"}
                )

        except AuthUnexpectedError as e:
            current_app.logger.exception(
                "Unexpected error during Google account unlinking",
                extra={"log_type": "auth"}
            )
            flash(str(e), "danger")
        except AuthError as e:
            flash(str(e), "danger")
        return redirect(url_for("auth.logout"))
    return redirect(url_for("auth.settings_account"))

@auth_bp.route("/google/reauth")
@login_required
def google_reauth():
    oauth = current_app.config["OAUTH"]

    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)

    session["reauth_state"] = state
    session["reauth_nonce"] = nonce

    redirect_uri = url_for("auth.google_reauth_callback", _external=True)

    return oauth.google.authorize_redirect(
        redirect_uri,
        state=state,
        nonce=nonce,
        prompt="login"
    )

@auth_bp.route("/google/reauth/callback")
@login_required
def google_reauth_callback():
    metrics.increment(MetricName.GOOGLE_OAUTH_CALLBACKS)

    oauth = current_app.config["OAUTH"]

    # Validate state
    state_in_session = session.pop("reauth_state", None)
    state_returned = request.args.get("state")
    if not state_in_session or not state_returned or state_in_session != state_returned:
        flash("Re-authentication failed. Please try again.", "danger")
        return redirect(url_for("auth.settings_account"))

    try:
        # Exchange code for tokens
        token = oauth.google.authorize_access_token()
    except OAuthError:
        flash("Authentication failed. Please try again.", "danger")
        return redirect(url_for("auth.settings_account"))

    # Parse and verify id_token (Authlib will validate the token)
    try:
        userinfo = oauth.google.parse_id_token(
            token,
            nonce=session.pop("reauth_nonce", None)
        )
    except Exception:
        flash("Failed to fetch account information from Google.", "danger")
        return redirect(url_for("auth.settings_account"))

    # Extract important claims
    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified", False)

    if not email or not google_id:
        flash("Google did not return required information", "danger")
        return redirect(url_for("auth.settings_account"))

    # Emails must match
    if email != current_user.email:
        flash("The Google account email must match your account email.", "warning")
        return redirect(url_for("auth.settings_account"))

    # Email must be verified
    if not email_verified:
        flash("Please verify your Google email before re-authenticating.", "warning")
        return redirect(url_for("auth.settings_account"))

    existing = get_user_by_google_id(google_id)
    if existing and existing.id != current_user.id:
        flash("This Google account is linked to another user.", "danger")
        return redirect(url_for("auth.settings_account"))

    # Redirect to the requested next
    next_url = session.pop("reauth_next", None)
    if next_url:
        # Grant a short-lived reauth proof in the session (use once)
        session["reauth_verified"] = True
        session["reauth_verified_at"] = time.time()

        current_app.logger.info(
            "Google re-authentication",
            extra={"log_type": "auth"}
        )

        return redirect(next_url)
    else:
        flash("Authentication failed. Please try again.", "danger")
        return redirect(url_for("auth.settings_account"))
