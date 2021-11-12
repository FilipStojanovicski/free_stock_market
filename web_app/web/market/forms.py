from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, NumberRange
from market.models import Users
from market.utils import round_data

class RegisterForm(FlaskForm):
    def validate_username(self, username_to_check):
        user = Users.query.filter_by(username=username_to_check.data).first()
        if user:
            raise ValidationError("Username already exists! Please try a different username")

    def validate_email_address(self, email_address_to_check):
        email_address = Users.query.filter_by(email_address=email_address_to_check.data).first()
        if email_address:
            raise ValidationError('Email Address already exists! Please try a different email address')

    username = StringField(label='User Name:', validators=[Length(min=2, max=30), DataRequired()])
    email_address = StringField(label='Email Address:', validators=[Email(), DataRequired()])
    password1 = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    password2 = PasswordField(label='Confirm Password:', validators=[EqualTo("password1"), DataRequired()])
    company = StringField(label='Company Name:', validators=[DataRequired()])
    submit = SubmitField(label='Create Account')

class LoginForm(FlaskForm):
    username = StringField(label = 'User Name:', validators=[DataRequired()])
    password = StringField(label = 'Password:', validators = [DataRequired()])
    submit = SubmitField(label='Sign In')

class PurchaseStockForm(FlaskForm):
    quantity = DecimalField(label = "Quantity:", validators = [DataRequired(), NumberRange(min=0)], places=2,
                filters=[lambda x: round_data(x, decimal_places = 2, rounding_type = "ROUND_DOWN")])
    submit = SubmitField(label='Purchase')

class SellStockForm(FlaskForm):
    quantity = DecimalField(label = 'Quantity:', validators = [DataRequired(), NumberRange(min=0)], places=2,
                filters=[lambda x: round_data(x, decimal_places = 2, rounding_type = "ROUND_DOWN")])
    submit = SubmitField(label='Sell')