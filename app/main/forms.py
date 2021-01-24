from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, StringField, IntegerField, \
    SelectField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, Optional
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
    # Have to remove the DataRequired to make the form work with TinyMCE
    # https://stackoverflow.com/questions/48838175/tinymce-an-invalid-form-control-with-name-content-is-not-focusable?noredirect=1&lq=1
    back = TextAreaField('Explanation', validators=[
        Length(min=1, max=1000)])
    deck = StringField('Deck', validators=[DataRequired(),
                                           Length(min=1, max=256)])
    next_date = DateField('Next Learn Date', validators=[Optional()],
                          format="%Y-%m-%d")
    bucket = SelectField('Bucket', default=1, coerce=int,
                         choices=list(zip(range(1, 7), range(1, 7))))
    submit = SubmitField('Submit')


class DeckForm(FlaskForm):
    name = TextAreaField('Name', validators=[
        DataRequired(), Length(min=1, max=500)])
    # Have to remove the DataRequired to make the form work with TinyMCE
    # https://stackoverflow.com/questions/48838175/tinymce-an-invalid-form-control-with-name-content-is-not-focusable?noredirect=1&lq=1
    description = TextAreaField('Description', validators=[
        Length(min=0, max=1000)])
    submit = SubmitField('Submit')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class BeforeLearningForm(FlaskForm):
    num_random_learned = IntegerField('Relearn',
                                      default=5)
    learn_date = DateField('Target Date', format="%Y-%m-%d")
    submit = SubmitField('Start')


class ClearLearningForm(FlaskForm):
    submit = SubmitField('Clear')


class LearningForm(FlaskForm):
    next = SubmitField('Next')
