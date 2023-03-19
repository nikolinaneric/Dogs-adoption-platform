from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, EmailField, SubmitField, RadioField, SelectMultipleField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from wtforms_alchemy import QuerySelectMultipleField
from flask_login import current_user
from .models import User


class UserFormSignUp(FlaskForm):
    email = EmailField("Email", validators = [DataRequired(), Length(min=4)])
    password1 = PasswordField("Password", validators = [DataRequired(), Length(min=8, message="Password must contain at least 8 characters")])
    password2 = PasswordField("Confirm Password", validators =[DataRequired(), Length(min=8), EqualTo('password1', message = "Passwords don't match!")])
    first_name = StringField("First name", validators = [DataRequired(), Length(min=3)])
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

    
class UserFormLogIn(FlaskForm):
    email = EmailField("Email", validators = [DataRequired(), Length(min=4)])
    password = PasswordField("Password", validators = [DataRequired(), Length(min=8, message="Password must contain at least 8 characters")])
    
class UserSetUp(FlaskForm):
    first_name = StringField('First name', validators = [Length(min=2, max=20)])
    email = EmailField('Email')
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg','png','jpeg'])])
    

class RequestResetForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')
    
    
class ResetPasswordForm(FlaskForm):
    password1 = PasswordField("Password", validators = [DataRequired(), Length(min=8, message="Password must contain at least 8 characters")])
    password2 = PasswordField("Confirm Password", validators =[DataRequired(), Length(min=8), EqualTo('password1', message = "Passwords don't match!")])
    submit = SubmitField('Submit new password')

class RequestVerificationForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    submit = SubmitField('Request Verification Mail')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class PostForm(FlaskForm):
    title = StringField('Name', validators=[DataRequired()])
    city =  StringField('City', validators=[DataRequired()])
    gender =  RadioField('Gender', choices = [('male','male'),('female', 'female')])
    data = TextAreaField('Description', validators=[DataRequired(), Length(max=300)])
    picture = FileField('Add a picture', validators=[FileAllowed(['jpg','png','jpeg'])])

    
