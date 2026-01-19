from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, DecimalField, IntegerField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class ProductForm(FlaskForm):
    name = StringField('Product Name',
                      validators=[DataRequired(), Length(min=1, max=100)],
                      render_kw={"placeholder": "Enter product name"})
    price = DecimalField('Price',
                        validators=[DataRequired(), NumberRange(min=0.01)],
                        places=2,
                        render_kw={"placeholder": "0.00", "step": "0.01"})
    stock_qty = IntegerField('Stock Quantity',
                           validators=[DataRequired(), NumberRange(min=0)],
                           render_kw={"placeholder": "0"})
    category = SelectField('Category',
                          choices=[
                              ('', '-- Select Category --'),
                              ('fruits', 'Fruits'),
                              ('vegetables', 'Vegetables'),
                              ('dairy', 'Dairy'),
                              ('meat', 'Meat'),
                              ('bakery', 'Bakery'),
                              ('beverages', 'Beverages'),
                              ('snacks', 'Snacks'),
                              ('household', 'Household'),
                              ('other', 'Other')
                          ],
                          validators=[DataRequired()])
    image = FileField('Product Image',
                     validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Save Product')


class EmployeeForm(FlaskForm):
    username = StringField('Username',
                          validators=[DataRequired(), Length(min=3, max=80)],
                          render_kw={"placeholder": "Enter username"})
    password = PasswordField('Password',
                           validators=[DataRequired(), Length(min=6)],
                           render_kw={"placeholder": "Enter password"})
    submit = SubmitField('Create Employee')

    def validate_username(self, username):
        from ..models import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')