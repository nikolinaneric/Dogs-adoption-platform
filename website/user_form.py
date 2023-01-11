from flask_wtf import FlaskForm
from wtforms import StringField,IntegerField, PasswordField, EmailField, RadioField
from wtforms.validators import InputRequired, DataRequired, NumberRange, Optional, Length, EqualTo

class UserFormSignUp(FlaskForm):
    email = EmailField("Email", validators = [DataRequired(), Length(min=4)])
    password1 = PasswordField("Password", validators = [DataRequired(), Length(min=8)])
    password2 = PasswordField("Confirm Password", validators =[DataRequired(), Length(min=8), EqualTo('password1', "not equal")])
    first_name = StringField("First name", validators = [DataRequired(), Length(min=3)])
    profile_type = RadioField("Profile type", choices = ['Person', 'Dog'], validators=[InputRequired()])
    