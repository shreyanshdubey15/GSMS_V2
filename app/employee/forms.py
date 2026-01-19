from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange


class AddToCartForm(FlaskForm):
    quantity = IntegerField('Quantity',
                          validators=[DataRequired(), NumberRange(min=1)],
                          default=1,
                          render_kw={"min": "1"})
    submit = SubmitField('Add to Cart')


class UpdateCartForm(FlaskForm):
    quantity = IntegerField('Quantity',
                          validators=[DataRequired(), NumberRange(min=0)],
                          render_kw={"min": "0"})
    submit = SubmitField('Update')


class CheckoutForm(FlaskForm):
    payment_method = SelectField('Payment Method',
                               choices=[('cash', 'Cash'), ('upi', 'UPI')],
                               validators=[DataRequired()])
    submit = SubmitField('Complete Order')