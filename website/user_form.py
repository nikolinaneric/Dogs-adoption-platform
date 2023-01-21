from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField,IntegerField, PasswordField, EmailField, RadioField
from wtforms.validators import InputRequired, DataRequired, NumberRange, Optional, Length, EqualTo, ValidationError
from flask_login import current_user
from .models import User

class UserFormSignUp(FlaskForm):
    email = EmailField("Email", validators = [DataRequired(), Length(min=4)])
    password1 = PasswordField("Password", validators = [DataRequired(), Length(min=8, message="Password must contain at least 8 characters")])
    password2 = PasswordField("Confirm Password", validators =[DataRequired(), Length(min=8), EqualTo('password1', message = "Passwords don't match!")])
    first_name = StringField("First name", validators = [DataRequired(), Length(min=3)])
    profile_type = RadioField("Profile type", choices = ['Person', 'Dog'], validators=[InputRequired()])
    

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

    
class UserFormLogIn(FlaskForm):
    email = EmailField("Email", validators = [DataRequired(), Length(min=4)])
    password = PasswordField("Password", validators = [DataRequired(), Length(min=8, message="Password must contain at least 8 characters")])
    
class UserSetUp(FlaskForm):
    first_name = StringField('First name', validators=[DataRequired(), Length(min=2, max=20)])
    email = EmailField('Email', validators=[DataRequired()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg','png'])])
    profile_type = RadioField("Profile type", choices = ['Person', 'Dog'], validators=[InputRequired()])
    

    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

    