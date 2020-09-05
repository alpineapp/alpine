from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, StringField, IntegerField, \
                    BooleanField
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
    back = TextAreaField('Explanation', validators=[
        DataRequired(), Length(min=1, max=1000)])
    deck = StringField('Deck', validators=[DataRequired(),
                                           Length(min=1, max=256)])
    start_date = DateField('Start Date', validators=[Optional()],
                           format="%Y-%m-%d")
    bucket = IntegerField('Bucket', default=1)
    example = TextAreaField('Example', validators=[
        Optional(), Length(min=1, max=2048)])
    use_case = TextAreaField('Use Case', validators=[
        Optional(), Length(min=1, max=2048)])
    source = TextAreaField('Source', validators=[
        Optional(), Length(min=1, max=2048)])
    reverse_asking = BooleanField('Reverse Asking', default=True)
    submit = SubmitField('Submit')


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class DeleteCardForm(FlaskForm):
    submit = SubmitField('Delete')


class StartLearningForm(FlaskForm):
    num_random_learned = IntegerField('Number of Random Re-learn Cards',
                                      default=5)
    learn_date = DateField('Target Date', format="%Y-%m-%d")
    submit = SubmitField('Start')


class ClearLearningForm(FlaskForm):
    submit = SubmitField('Clear')


class LearningForm(FlaskForm):
    not_ok = SubmitField('Not OK')
    ok = SubmitField('OK')
    next = SubmitField('Next')
