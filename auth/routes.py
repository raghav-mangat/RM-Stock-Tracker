from . import auth_bp
from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from models.database import User
from .forms import LoginForm, SignupForm, ResetPasswordRequestForm, ResetPasswordForm
from .emails import send_password_reset_email, send_verify_user_email, send_user_verification_success_email
from utils.db_queries.user_data import get_user_by_email, add_new_user, change_user_password, verify_user

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))
    form = SignupForm()
    if form.validate_on_submit():
        user = add_new_user(
            name=form.username.data,
            email=form.email.data,
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

@auth_bp.route("/reset_password/<string:token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("watchlist.index"))

    user = User.verify_token(token, token_type="reset_password")
    if not user:
        flash("The reset password link is invalid or has expired. Please request a new link to reset password.",
              "danger")
        return redirect(url_for("auth.login"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        change_user_password(user, form.password.data)
        flash("Your password has been reset.", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html", form=form)

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
    flash("Thanks, your email is verified!. You are now logged in.", "success")
    login_user(user)
    return redirect(url_for("watchlist.index"))
