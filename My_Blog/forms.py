# forms.py

from flask_wtf import FlaskForm as Form
from wtforms import StringField, PasswordField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(Form):
    username = StringField('Username', [DataRequired(), Length(max=255)])
    password = PasswordField('Password', [DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField('Login')

class RegisterForm(Form):
    username = StringField('Username', [DataRequired(), Length(max=255)])
    password = PasswordField('Password', [DataRequired(), Length(min=6)])

class CommentForm(Form):
    name = StringField('Name',validators=[DataRequired(), Length(max=255)])
    text = TextAreaField(u'Comment', validators=[DataRequired()])

class PostForm(Form):
    title = StringField('Title', [DataRequired(), Length(max=255)])
    text = TextAreaField('Content', [DataRequired()])
