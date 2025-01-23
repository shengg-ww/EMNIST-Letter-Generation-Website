from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length, Email, NumberRange, ValidationError


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class ForgetPasswordForm(FlaskForm):
    # Step 1: Email input
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid Email Address')])
    submit_email = SubmitField('Submit Email')

    # Step 2: Password reset inputs
    new_password = PasswordField('New Password', validators=[DataRequired(),Length(min=3, message="Password must be at least 3 characters long")])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')]
    )
    submit_password = SubmitField('Reset Password')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=20, message="Username must be between 3 and 20 characters")
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message="Invalid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=3, message="Password must be at least 3 characters long")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Register')