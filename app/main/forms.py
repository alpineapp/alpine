from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, StringField
from wtforms.validators import DataRequired, Length
from flask import request


class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class CardForm(FlaskForm):
    front = TextAreaField('Definition', validators=[
        DataRequired(), Length(min=1, max=500)])
    back = TextAreaField('Explanation', validators=[
        DataRequired(), Length(min=1, max=1000)])
    deck = StringField('Deck', validators=[DataRequired(),
                                           Length(min=1, max=256)])
    submit = SubmitField('Submit')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class DeleteCardForm(FlaskForm):
    submit = SubmitField('Delete')
