from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import current_user
import re
from utils.constants import PASSWORD_POLICY, USERNAME_POLICY, NAME_POLICY
from utils.db_queries.user_data import get_user_by_email, get_user_by_username

def normalize_email(email):
    return email.strip().lower() if email else email

def normalize_name(name):
    return name.strip() if name else name

def normalize_username(username):
    return username.strip().lower() if username else username

def normalize_password(password):
    return password.strip() if password else password

def check_password_strength(form, field):
    raw_password = field.raw_data[0] if field.raw_data else ""

    # Check leading/trailing spaces
    if raw_password != raw_password.strip():
        raise ValidationError("Password cannot start or end with spaces")

    password = field.data
    policy = PASSWORD_POLICY

    if len(password) < policy["min_length"]:
        raise ValidationError(
            f"Password must be at least {policy['min_length']} characters long"
        )

    if len(password) > policy["max_length"]:
        raise ValidationError(
            f"Password must be at most {policy['max_length']} characters long"
        )

    if policy["require_upper"] and not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter")

    if policy["require_lower"] and not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter")

    if policy["require_number"] and not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one number")

    if policy["require_special"] and not re.search(
        policy["special_chars_regex"], password
    ):
        raise ValidationError(
            "Password must contain at least one special character (e.g., !@#$...)"
        )

def get_email_field():
    email = StringField('Email', filters=[normalize_email], validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email address")
    ])
    return email

def get_first_name_field():
    max_name_len = NAME_POLICY.get("max_length", "")
    first_name = StringField('First Name', filters=[normalize_name], validators=[
        DataRequired(message="First name is required"),
        Length(max=max_name_len, message=f"First name must be at most {max_name_len} characters long")
    ])
    return first_name

def get_last_name_field():
    max_name_len = NAME_POLICY.get("max_length", "")
    last_name = StringField('Last Name', filters=[normalize_name], validators=[
        DataRequired(message="Last name is required"),
        Length(max=max_name_len, message=f"Last name must be at most {max_name_len} characters long")
    ])
    return last_name

def get_username_field():
    min_username_len = USERNAME_POLICY.get("min_length", "")
    max_username_len = USERNAME_POLICY.get("max_length", "")
    username = StringField('Username', filters=[normalize_username], validators=[
        DataRequired(message="Username is required"),
        Length(
            min=min_username_len,
            max=max_username_len,
            message=f"Username must be between {min_username_len} and {max_username_len} characters long"),
    ])
    return username

def get_password_field(label="Password", validate_strong_password=False):
    validators = [DataRequired(message="Password is required")]
    if validate_strong_password:
        validators.append(check_password_strength)

    password = PasswordField(label, filters=[normalize_password], validators=validators)
    return password

def get_confirm_password_field(password_field):
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo(password_field, message="Passwords must match")
    ])
    return confirm_password

def validate_first_name_field(field):
    if not re.match(NAME_POLICY.get("allowed_chars_regex", ""), field.data):
        raise ValidationError("First name can only contain letters, spaces, hyphens (-), and apostrophes (')")

def validate_last_name_field(field):
    if not re.match(NAME_POLICY.get("allowed_chars_regex", ""), field.data):
        raise ValidationError("Last name can only contain letters, spaces, hyphens (-), and apostrophes (')")

def validate_username_field(field):
    username = field.data

    # Must start with letter
    if USERNAME_POLICY["start_with_letter"] and not username[0].isalpha():
        raise ValidationError("Username must start with a letter")

    # Allowed characters
    if not re.match(USERNAME_POLICY["allowed_chars_regex"], username):
        raise ValidationError(
            "Username can only contain lowercase letters, numbers, and special characters like "
            "dots(.), underscores(_) and hyphens(-)"
        )

    # No consecutive special characters
    if USERNAME_POLICY["no_consecutive_special"]:
        if re.search(rf"[{USERNAME_POLICY['special_chars']}]{{{2}}}", username):
            raise ValidationError(
                "Username cannot contain consecutive special characters"
            )

    # No trailing special character
    if USERNAME_POLICY["no_trailing_special"]:
        if username[-1] in USERNAME_POLICY["special_chars"]:
            raise ValidationError(
                "Username cannot end with a special character ( . , _ , -)"
            )

    # Uniqueness check
    user = get_user_by_username(username)
    if user:
        raise ValidationError("This username is already taken, please choose another")


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
    toggle_email_alerts_submit = SubmitField("Confirm")

class SettingsSetPasswordForm(FlaskForm):
    password = get_password_field(label="Password", validate_strong_password=True)
    confirm_password = get_confirm_password_field("password")
    submit = SubmitField("Set Password")

class SettingsResetPasswordRequestForm(FlaskForm):
    reset_password_submit = SubmitField("Send Reset Link")

class SettingsRemovePasswordForm(FlaskForm):
    remove_password = get_password_field()
    remove_password_submit = SubmitField("Remove Password")

class SettingsUnlinkGoogleAccountForm(FlaskForm):
    unlink_google_password = get_password_field()
    unlink_google_submit = SubmitField("Unlink Google Account")

class SettingsDeleteAccountRequestForm(FlaskForm):
    delete_account_password = get_password_field()
    delete_account_submit = SubmitField("Send Deletion Link")

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

class ResetPasswordForm(FlaskForm):
    password = get_password_field(label="New Password", validate_strong_password=True)
    confirm_password = get_confirm_password_field("password")
    submit = SubmitField("Reset Password")

class DeleteAccountForm(FlaskForm):
    email = get_email_field()
    submit = SubmitField("Delete Account")
