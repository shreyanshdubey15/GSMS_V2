from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, ValidationError


class LoginForm(FlaskForm):
    username = StringField('Username',
                          validators=[DataRequired(), Length(min=3, max=80)],
                          render_kw={"placeholder": "Enter your username"})
    password = PasswordField('Password',
                           validators=[DataRequired()],
                           render_kw={"placeholder": "Enter your password"})
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')

    def validate_username(self, username):
        from ..models import User
        user = User.query.filter_by(username=username.data).first()
        if not user:
            raise ValidationError('Invalid username or password.')

    def validate_password(self, password):
        from ..models import User
        user = User.query.filter_by(username=self.username.data).first()
        if user and not user.check_password(password.data):
            raise ValidationError('Invalid username or password.')