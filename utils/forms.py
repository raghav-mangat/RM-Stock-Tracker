from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import check_password_hash
from utils.db_queries.user_data import get_user_by_email, get_user_by_name

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    submit = SubmitField("Log In")

    def validate_email(self, field):
        user = get_user_by_email(field.data)
        if not user:
            raise ValidationError("No account found with this email address")

    def validate_password(self, field):
        user = get_user_by_email(self.email.data)
        if user and not check_password_hash(user.password_hash, field.data):
            raise ValidationError("Incorrect password")

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(max=50, message="Username must be at most 50 characters long")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Enter a valid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
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

    def validate_username(self, field):
        user = get_user_by_name(field.data)
        if user:
            raise ValidationError("This username is already taken. Please choose another")
