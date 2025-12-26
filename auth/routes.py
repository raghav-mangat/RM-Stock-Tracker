from . import auth_bp
from flask import render_template, redirect, url_for, flash, session, request, current_app
from flask_login import current_user, login_user, login_required, logout_user
from authlib.integrations.flask_client import OAuthError
import secrets
import time
from models.database import User, SignupSource
from .emails import AuthEmail
from .services import RedirectService
from .forms import (
    LoginForm, SignupForm, ResetPasswordRequestForm, ResetPasswordForm, ProfileSettingsForm,
    DeleteAccountRequestForm, DeleteAccountForm, SettingsResetPasswordRequestForm, UnlinkGoogleAccountForm,
    SettingsSetPasswordForm, SettingsRemovePasswordForm, SettingsToggleEmailAlertsForm
)
from utils.db_queries.user_data import (
    add_new_user, update_user_profile, change_user_password, verify_user,
    get_user_by_email, get_user_by_google_id, delete_user_account, add_user_google_id, remove_user_google_id,
    remove_user_password, update_user_last_login_at, toggle_user_email_alerts_on
)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))
    form = SignupForm()
    if form.validate_on_submit():
        user = add_new_user(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            username=form.username.data,
            password=form.password.data,
            signup_source=SignupSource.EMAIL
        )
        AuthEmail.verify_email(user)
        flash("Account created, we sent a verification email. Please click the link in your inbox (check spam).", "success")
        return redirect(url_for('auth.login'))

    return render_template("signup.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)

        if not user.is_verified:
            AuthEmail.verify_email(user)
            flash("Account not verified. We have sent a verification email, please check your inbox (and spam).",
                  "warning")
            return redirect(url_for('auth.login'))

        login_user(user)
        update_user_last_login_at(user)
        session["security_timestamp"] = user.security_timestamp

        flash("Logged in successfully!", "success")

        return redirect(RedirectService.get_post_login_redirect())

    return render_template("login.html", form=form)

@auth_bp.route("/logout")
def logout():
    session.pop("security_timestamp", None)
    session.pop("reauth_verified", None)
    session.pop("reauth_verified_at", None)

    logout_user()

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
        update_user_profile(
            user=current_user,
            first_name=profile_settings_form.first_name.data,
            last_name=profile_settings_form.last_name.data,
            username=profile_settings_form.username.data
        )
        flash("Profile updated successfully.", "success")
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
        unlink_google_account_form=UnlinkGoogleAccountForm(),
        settings_reset_password_request_form=SettingsResetPasswordRequestForm(
            email=current_user.email
        ),
        settings_remove_password_form=SettingsRemovePasswordForm(),
        delete_account_request_form=DeleteAccountRequestForm(
            email=current_user.email
        ),
    )

@auth_bp.route("/verify_email/<string:token>", methods=["GET"])
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

    verify_user(user)
    AuthEmail.user_verification_success(user)
    flash("Your email is verified! Now you can log in.", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if user:
            AuthEmail.reset_password(user)
        flash("Check your email for the instructions to reset your password.", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password_request.html", form=form)

@auth_bp.route("/settings_toggle_email_alerts", methods=["POST"])
@login_required
def settings_toggle_email_alerts():
    form = SettingsToggleEmailAlertsForm()

    if form.validate_on_submit():
        toggle_user_email_alerts_on(current_user)
        if current_user.email_alerts_on:
            flash("Email alerts have been turned ON.", "success")
        else:
            flash("Email alerts have been turned OFF.","success")
    else:
        flash("Invalid request.", "danger")

    return redirect(url_for("auth.settings_account"))

@auth_bp.route("/settings/set_password", methods=["GET", "POST"])
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
            flash("Your verification expired. Please try again.", "warning")
            return redirect(url_for("auth.settings_account"))
        if form.validate_on_submit():
            # Consume reauth proof
            session.pop("reauth_verified", None)
            session.pop("reauth_verified_at", None)

            change_user_password(current_user, form.password.data)
            AuthEmail.settings_password_set_success(current_user)

            flash("Your password has been set. Please log in again.", "success")
            return redirect(url_for("auth.logout"))

    if reauth_expired:
        session["reauth_next"] = url_for(
            "auth.settings_set_password", _external=True
        )
        return redirect(url_for("auth.google_reauth"))

    return render_template("settings_set_password.html", form=form)

@auth_bp.route("/settings_reset_password_request", methods=["POST"])
@login_required
def settings_reset_password_request():
    form = SettingsResetPasswordRequestForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if user:
            AuthEmail.settings_reset_password(user)
        flash("Check your email for the instructions to reset your password.", "success")
    return redirect(url_for("auth.settings_account"))

@auth_bp.route("/settings_remove_password", methods=["POST"])
@login_required
def settings_remove_password():
    form = SettingsRemovePasswordForm()

    if not current_user.password_hash:
        flash("You must set a password before removing your password.", "danger")
    elif not current_user.google_id:
        flash("You must link your Google account before removing your password.", "warning")
    elif not form.validate_on_submit():
        flash("Please enter your password.", "warning")
    elif not current_user.verify_password(form.password.data):
        flash("Incorrect password.", "warning")
    else:
        remove_user_password(current_user)
        AuthEmail.settings_password_removed_success(current_user)
        flash("Your password has been removed. Please log in again.", "success")
        return redirect(url_for("auth.logout"))
    return redirect(url_for("auth.settings_account"))

@auth_bp.route("/reset_password/<string:token>", methods=["GET", "POST"])
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
        change_user_password(user, form.password.data)
        AuthEmail.password_reset_success(user)
        flash("Your password has been reset. Please log in again.", "success")
        return redirect(url_for("auth.logout"))

    return render_template("reset_password.html", form=form)

@auth_bp.route("/delete_account_request", methods=["POST"])
@login_required
def delete_account_request():
    form = DeleteAccountRequestForm()

    email = form.email.data
    if not email or email != current_user.email:
        flash("Incorrect email.", "danger")
        return redirect(url_for("auth.settings_account"))

    if current_user.password_hash:
        # User must enter password
        if not form.validate_on_submit():
            flash("Please enter your password.", "warning")
            return redirect(url_for("auth.settings_account"))

        if not current_user.verify_password(form.password.data):
            flash("Incorrect password.", "warning")
            return redirect(url_for("auth.settings_account"))

    # If no password exists, skip password check
    AuthEmail.delete_account(current_user)
    flash("Check your email for the instructions to delete your account.", "success")
    return redirect(url_for("auth.settings_account"))

@auth_bp.route("/delete_account/<string:token>", methods=["GET", "POST"])
def delete_account(token):
    user = User.verify_token(token, token_type="delete_account")
    if not user:
        flash("The delete account link is invalid or has expired. Please request a new link to delete your account.",
              "danger")
        return redirect(url_for("auth.login"))

    form = DeleteAccountForm()
    if form.validate_on_submit():
        if user.email == form.email.data:
            delete_user_account(user)
            AuthEmail.account_delete_success(user)
            flash("Your account has been deleted.", "success")
            return redirect(url_for("auth.logout"))
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

    # Find or create user (linking if same email exists)
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
                add_user_google_id(user, google_id)
                AuthEmail.google_account_linked_success(user)
                flash("Signed in with Google. Linked Google account successfully.", "success")
    else:
        user = add_new_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=None,
            password=None,
            google_id=google_id,
            is_verified=True,
            signup_source=SignupSource.GOOGLE
        )
        AuthEmail.google_signin_success(user)
        flash("Signed in with Google. Account created successfully.", "success")
        return redirect(url_for("watchlist.index"))

    login_user(user)
    update_user_last_login_at(user)
    session["security_timestamp"] = user.security_timestamp

    # Restore next url safely
    next_url = session.pop("oauth_next", None)
    if next_url and RedirectService.is_safe_redirect_url(next_url):
        return redirect(next_url)

    return redirect(url_for("watchlist.index"))

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

    add_user_google_id(current_user, google_id)
    AuthEmail.google_account_linked_success(current_user)
    flash("Google account linked successfully. Please log in again.", "success")
    return redirect(url_for("auth.logout"))

@auth_bp.route("/google/unlink", methods=["POST"])
@login_required
def google_unlink():
    form = UnlinkGoogleAccountForm()

    if not current_user.password_hash:
        flash("You must set a password before unlinking your Google account.", "warning")
    elif not form.validate_on_submit():
        flash("Please enter your password.", "warning")
    elif not current_user.verify_password(form.password.data):
        flash("Incorrect password.", "warning")
    else:
        remove_user_google_id(current_user)
        AuthEmail.google_account_unlinked_success(current_user)
        flash("Your Google account has been unlinked. Please log in again.", "success")
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
        flash("Re-authentication successful.", "success")
        return redirect(next_url)
    else:
        flash("Authentication failed. Please try again.", "danger")
        return redirect(url_for("auth.settings_account"))
