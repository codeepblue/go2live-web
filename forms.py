from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import data_required, length, any_of, optional


class LoginForm(FlaskForm):
    email = StringField("email", id="email", validators=[data_required()])
    password = PasswordField("password", id="password", validators=[data_required(), length(min=8, max=16)])


class CreateLiveForm(FlaskForm):
    title = StringField("title", id="title", validators=[data_required(), length(min=3, max=255)])


class UpdateLiveForm(FlaskForm):
    password = StringField("password", id="password", validators=[length(min=3, max=20), optional()])
    expires_in = IntegerField("expires_in", id="expires_in", validators=[any_of([0, 1, 7, 15, 30])])


class RegisterUserForm(FlaskForm):
    username = StringField("username", id="username", validators=[data_required()])
    email = StringField("email", id="email", validators=[data_required()])
    password = PasswordField("password", id="password", validators=[data_required(), length(min=8, max=16)])
    confirm_password = PasswordField("confirm_password", id="password", default="",
                                     validators=[data_required(), length(min=8, max=16)])


class AuthenticateWatcher(FlaskForm):
    nickname = StringField("nickname", id="nickname", validators=[data_required()])
    password = PasswordField("password", id="password")
