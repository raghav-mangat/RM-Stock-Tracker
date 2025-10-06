from . import auth_bp
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash
from utils.db_queries.user_data import get_user_by_email, add_new_user
from .forms import LoginForm, SignupForm

@auth_bp.route('/signup', methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        name = form.username.data
        email = form.email.data
        password_hash = hash_and_salted_password

        user = add_new_user(
            name=name,
            email=email,
            password_hash=password_hash
        )

        flash("Account created successfully!", "success")
        login_user(user)
        return redirect(url_for('watchlist.index'))

    return render_template("signup.html", form=form)

@auth_bp.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        login_user(user)
        flash("Logged in successfully!", "success")
        return redirect(url_for('watchlist.index'))

    return render_template("login.html", form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('home'))
