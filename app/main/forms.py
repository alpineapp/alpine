from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class CardForm(FlaskForm):
    front = TextAreaField('Definition', validators=[
        DataRequired(), Length(min=1, max=140)])
    back = TextAreaField('Explanation', validators=[
        DataRequired(), Length(min=1, max=300)])
    submit = SubmitField('Submit')
