from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import current_user
import re
from utils.constants import PASSWORD_SPECIAL_CHARS_REGEX, NAME_REGEX, USERNAME_REGEX, MIN_USERNAME_LEN, MAX_USERNAME_LEN, MAX_NAME_LEN
from utils.db_queries.user_data import get_user_by_email, get_user_by_username

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

def get_email_field():
    email = StringField('Email', filters=[normalize_email], validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email address")
    ])
    return email

def get_first_name_field():
    first_name = StringField('First Name', filters=[normalize_name], validators=[
        DataRequired(message="First name is required"),
        Length(max=MAX_NAME_LEN, message=f"First name must be at most {MAX_NAME_LEN} characters long")
    ])
    return first_name

def get_last_name_field():
    last_name = StringField('Last Name', filters=[normalize_name], validators=[
        DataRequired(message="Last name is required"),
        Length(max=MAX_NAME_LEN, message=f"Last name must be at most {MAX_NAME_LEN} characters long")
    ])
    return last_name

def get_username_field():
    username = StringField('Username', filters=[normalize_username], validators=[
        DataRequired(message="Username is required"),
        Length(
            min=MIN_USERNAME_LEN,
            max=MAX_USERNAME_LEN,
            message=f"Username must be between {MIN_USERNAME_LEN} and {MAX_USERNAME_LEN} characters"),
    ])
    return username

def get_password_field(label="Password", validate_strong_password=False):
    validators = [DataRequired(message="Password is required")]
    if validate_strong_password:
        validators.append(strong_password)

    password = PasswordField(label, validators=validators)
    return password

def get_confirm_password_field(password_field):
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo(password_field, message="Passwords must match")
    ])
    return confirm_password

def validate_first_name_field(field):
    if not re.match(NAME_REGEX, field.data):
        raise ValidationError("Only alphabetic characters allowed in first name")

def validate_last_name_field(field):
    if not re.match(NAME_REGEX, field.data):
        raise ValidationError("Only alphabetic characters allowed in last name")

def validate_username_field(field):
    if not re.match(USERNAME_REGEX, field.data):
        raise ValidationError(
            "Username must start with a letter and contain only letters, numbers, dots, hyphens or underscores"
        )
    user = get_user_by_username(field.data)
    if user:
        raise ValidationError("This username is already taken. Please choose another")


class LoginForm(FlaskForm):
    email = get_email_field()
    password = get_password_field()
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
    first_name = get_first_name_field()
    last_name = get_last_name_field()
    email = get_email_field()
    username = get_username_field()
    password = get_password_field(validate_strong_password=True)
    confirm_password = get_confirm_password_field("password")
    submit = SubmitField("Sign Up")

    def validate_email(self, field):
        user = get_user_by_email(field.data)
        if user:
            raise ValidationError("An account with this email already exists")

    def validate_first_name(self, field):
        validate_first_name_field(field)

    def validate_last_name(self, field):
        validate_last_name_field(field)

    def validate_username(self, field):
        validate_username_field(field)

class ChooseUsernameForm(FlaskForm):
    username = get_username_field()
    submit = SubmitField("Sign Up")

    def validate_username(self, field):
        validate_username_field(field)

class ResetPasswordRequestForm(FlaskForm):
    email = get_email_field()
    submit = SubmitField("Request Password Reset")

class SettingsToggleEmailAlertsForm(FlaskForm):
    submit = SubmitField("Confirm")

class SettingsSetPasswordForm(FlaskForm):
    password = get_password_field(label="Password", validate_strong_password=True)
    confirm_password = get_confirm_password_field("password")
    submit = SubmitField("Set Password")

class SettingsResetPasswordRequestForm(FlaskForm):
    email = HiddenField("Email")
    submit = SubmitField("Send Reset Link")

class SettingsRemovePasswordForm(FlaskForm):
    password = get_password_field()
    submit = SubmitField("Remove Password")

class ResetPasswordForm(FlaskForm):
    password = get_password_field(label="New Password", validate_strong_password=True)
    confirm_password = get_confirm_password_field("password")
    submit = SubmitField("Reset Password")

class ProfileSettingsForm(FlaskForm):
    first_name = get_first_name_field()
    last_name = get_last_name_field()
    username = get_username_field()

    def validate_first_name(self, field):
        validate_first_name_field(field)

    def validate_last_name(self, field):
        validate_last_name_field(field)

    def validate_username(self, field):
        if field.data == current_user.username:
            return
        validate_username_field(field)

class UnlinkGoogleAccountForm(FlaskForm):
    password = get_password_field()
    submit = SubmitField("Unlink Google Account")

class DeleteAccountRequestForm(FlaskForm):
    password = get_password_field()
    email = HiddenField("Email")
    submit = SubmitField("Send Deletion Link")

class DeleteAccountForm(FlaskForm):
    email = get_email_field()
    submit = SubmitField("Delete Account")
