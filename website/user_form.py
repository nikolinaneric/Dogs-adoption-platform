from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, EmailField, SubmitField, RadioField, SelectMultipleField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from wtforms_alchemy import QuerySelectMultipleField
from flask_login import current_user
from .models import User
from flask_babel import gettext

class UserFormSignUp(FlaskForm):
    email = EmailField(gettext("Email"), validators = [DataRequired(), Length(min=4)])
    password1 = PasswordField(gettext("Password"), validators = [DataRequired(), Length(min=8, message="Password must contain at least 8 characters")])
    password2 = PasswordField(gettext("Confirm Password"), validators =[DataRequired(), Length(min=8), EqualTo('password1', message = "Passwords don't match!")])
    first_name = StringField(gettext("First name"), validators = [DataRequired(), Length(min=3)])

    
class UserFormLogIn(FlaskForm):
    email = EmailField(gettext("Email"), validators = [DataRequired(), Length(min=4)])
    password = PasswordField(gettext("Password"), validators = [DataRequired(), Length(min=8, message=gettext("Password must contain at least 8 characters"))])
    
class UserSetUp(FlaskForm):
    first_name = StringField(gettext('First name'), validators = [Length(min=2, max=20)])
    email = EmailField(gettext('Email'))
    picture = FileField(gettext('Update Profile Picture'), validators=[FileAllowed(['jpg','png','jpeg'])])
    

class RequestResetForm(FlaskForm):
    email = EmailField(gettext('Email'), validators=[DataRequired()])
    submit = SubmitField(gettext('Request Password Reset'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')
    
    
class ResetPasswordForm(FlaskForm):
    password1 = PasswordField(gettext("Password"), validators = [DataRequired(), Length(min=8, message=gettext("Password must contain at least 8 characters"))])
    password2 = PasswordField(gettext("Confirm Password"), validators =[DataRequired(), Length(min=8), EqualTo('password1', message = gettext("Passwords don't match!"))])
    submit = SubmitField(gettext('Submit new password'))

class RequestVerificationForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    submit = SubmitField(gettext('Request Verification Mail'))

class PostForm(FlaskForm):
    title = StringField(gettext('Name'), validators=[DataRequired()])
    city =  StringField(gettext('City'), validators=[DataRequired()])
    gender =  RadioField(gettext('Gender'), choices = [('male','male'),('female', 'female')])
    data = TextAreaField(gettext('Description'), validators=[DataRequired(), Length(max=300)])
    picture = FileField(gettext('Add a picture'), validators=[FileAllowed(['jpg','png','jpeg'])])

    
