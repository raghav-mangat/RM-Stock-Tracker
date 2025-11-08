from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import re
from utils.db_queries.user_data import get_user_by_email, get_user_by_username

PASSWORD_SPECIAL_CHARS_REGEX = r"[!@#$%^&*()_\-+=|\\{}\[\]:;\"'<>,.?/~` ]"
NAME_REGEX = r"^[A-Za-zÀ-ÖØ-öø-ÿ'’.-]+$"
USERNAME_REGEX = r"^[a-z][a-z0-9._-]+$"

def normalize_email(email):
    return email.strip().lower() if email else email

def normalize_name(name):
    return name.strip().title() if name else name

def normalize_username(username):
    return username.strip().lower() if username else username

def strong_password(form, field):
    password = field.data

    # Requirements checks
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")

    if len(password) > 256:
        raise ValidationError("Password must be at most 256 characters long")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter")

    if not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one number")

    if not re.search(PASSWORD_SPECIAL_CHARS_REGEX, password):
        raise ValidationError("Password must contain at least one special character (e.g., !@#$...)")

class LoginForm(FlaskForm):
    email = StringField('Email', filters=[normalize_email], validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email address")
    ])

    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
    ])

    submit = SubmitField("Log In")

    def validate_email(self, field):
        user = get_user_by_email(field.data)
        if not user:
            raise ValidationError("No account found with this email address")

    def validate_password(self, field):
        user = get_user_by_email(self.email.data)
        if user and not user.verify_password(field.data):
            raise ValidationError("Incorrect password")

class SignupForm(FlaskForm):
    first_name = StringField('First Name', filters=[normalize_name], validators=[
        DataRequired(message="First name is required"),
        Length(max=50, message="First name must be at most 50 characters long")
    ])

    last_name = StringField('Last Name', filters=[normalize_name], validators=[
        DataRequired(message="Last name is required"),
        Length(max=50, message="Last name must be at most 50 characters long")
    ])

    email = StringField('Email', filters=[normalize_email], validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email address")
    ])

    username = StringField('Username', filters=[normalize_username], validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=30, message="Username must be between 3 and 30 characters"),
    ])

    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        strong_password
    ])

    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])

    submit = SubmitField("Sign Up")

    def validate_email(self, field):
        user = get_user_by_email(field.data)
        if user:
            raise ValidationError("An account with this email already exists")

    def validate_first_name(self, field):
        if not re.match(NAME_REGEX, field.data):
            raise ValidationError("Only alphabetic characters allowed in first name")

    def validate_last_name(self, field):
        if not re.match(NAME_REGEX, field.data):
            raise ValidationError("Only alphabetic characters allowed in last name")

    def validate_username(self, field):
        if not re.match(USERNAME_REGEX, field.data):
            raise ValidationError(
                "Username must start with a letter and contain only letters, numbers, dots, hyphens or underscores"
            )

        user = get_user_by_username(field.data)
        if user:
            raise ValidationError("This username is already taken")

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', filters=[normalize_email], validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email address")
    ])
    submit = SubmitField("Request Password Reset")

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(message="Password is required"),
        strong_password
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField("Reset Password")