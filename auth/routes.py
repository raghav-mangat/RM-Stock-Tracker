from . import auth_bp
from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from models.database import User
from .forms import LoginForm, SignupForm, ResetPasswordRequestForm, ResetPasswordForm, ProfileSettingsForm, DeleteAccountRequestForm, DeleteAccountForm, SettingsResetPasswordRequestForm
from .emails import send_password_reset_email, send_verify_user_email, send_password_reset_success_email, send_user_verification_success_email, send_delete_account_email, send_account_delete_success_email, send_settings_password_reset_email
from utils.db_queries.user_data import add_new_user, update_user_profile, change_user_password, verify_user, get_user_by_email, delete_user_account

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
            password=form.password.data
        )
        send_verify_user_email(user)
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
            send_verify_user_email(user)
            flash("Account not verified. We have sent a verification email, please check your inbox (and spam).",
                  "warning")
            return redirect(url_for('auth.login'))
        login_user(user)
        flash("Logged in successfully!", "success")
        return redirect(url_for('watchlist.index'))

    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('home'))

@auth_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    profile_settings_form = ProfileSettingsForm(obj=current_user)

    settings_reset_password_request_form = SettingsResetPasswordRequestForm()
    settings_reset_password_request_form.email.data = current_user.email

    delete_account_request_form = DeleteAccountRequestForm()
    delete_account_request_form.email.data = current_user.email

    if profile_settings_form.validate_on_submit():
        update_user_profile(
            user=current_user,
            first_name=profile_settings_form.first_name.data,
            last_name=profile_settings_form.last_name.data,
            username=profile_settings_form.username.data
        )
        flash("Profile updated successfully", "success")
        return redirect(url_for("auth.settings"))

    return render_template(
        "settings.html",
        profile_settings_form=profile_settings_form,
        settings_reset_password_request_form=settings_reset_password_request_form,
        delete_account_request_form=delete_account_request_form
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
    send_user_verification_success_email(user)
    flash("Your email is verified! Now you can Log In.", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if user:
            send_password_reset_email(user)
        flash("Check your email for the instructions to reset your password.", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password_request.html", form=form)

@auth_bp.route("/settings_reset_password_request", methods=["POST"])
@login_required
def settings_reset_password_request():
    form = SettingsResetPasswordRequestForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if user:
            send_settings_password_reset_email(user)
        flash("Check your email for the instructions to reset your password.", "success")
    return redirect(url_for("auth.settings"))

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
        send_password_reset_success_email(user)
        flash_text = "Your password has been reset."

        if current_user.is_authenticated and current_user.id == user.id:
            logout_user()
            flash_text += " You have now been logged out."

        flash(flash_text, "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html", form=form)

@auth_bp.route("/delete_account_request", methods=["POST"])
@login_required
def delete_account_request():
    form = DeleteAccountRequestForm()
    if form.validate_on_submit:
        user = get_user_by_email(form.email.data)
        if not user:
            flash("Invalid user.", "danger")
        else:
            if user.verify_password(form.password.data):
                send_delete_account_email(user)
                flash("Check your email for the instructions to delete your account.", "success")
            else:
                flash("Incorrect password.", "warning")
    return redirect(url_for("auth.settings"))

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
            if current_user.is_authenticated and current_user.id == user.id:
                logout_user()
            send_account_delete_success_email(user)
            flash("Your account has been deleted.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Incorrect email to delete account.", "warning")
            return redirect(url_for("auth.delete_account", token=token))
    return render_template("delete_account.html", form=form)