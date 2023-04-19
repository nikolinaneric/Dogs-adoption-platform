from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, RadioField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length
from flask_babel import gettext


class PostForm(FlaskForm):
    title = StringField(gettext('Name'), validators=[DataRequired()])
    city =  StringField(gettext('City'), validators=[DataRequired()])
    gender =  RadioField(gettext('Gender'), choices = [('male','male'),('female', 'female')], render_kw={'class': 'form-radio'})
    data = TextAreaField(gettext('Description'), validators=[DataRequired(), Length(max=300)])
    picture = FileField(gettext('Add a picture'), validators=[FileAllowed(['jpg','png','jpeg'])])



