from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import (StringField, PasswordField, SubmitField, 
                    BooleanField, TextAreaField, IntegerField, SelectField)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from covid19.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Full Name',validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    contact = IntegerField('Contact No.',validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    address = StringField('Address',validators=[DataRequired()])                                 
    city = StringField('City',validators=[DataRequired()])
    resources = SelectField(u'Resources You Can Provide/Arrange', 
                            choices=[('','None'),('Blood', 'Blood'),('Plasma', 'Plasma'),
                            ('Oxygen', 'Oxygen'),('Hospital Bed', 'Hospital Bed'),
                            ('Covid Bed', 'Covid Bed'),('Medicine', 'Medicine'),
                            ('Ambulance', 'Ambulance'), ('Home Care', 'Home Care')])
    volunteer = SelectField(u'Do You Want to Volunteer With Us',choices=[('Yes','Yes'),('No','No')])
    feedback = StringField('Tell Us How We Can Improve')

    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    contact = IntegerField('Contact No.',validators=[DataRequired()])           
    address = StringField('Address',validators=[DataRequired()])                                 
    city = StringField('City',validators=[DataRequired()])
    resources = SelectField(u'Resources You Can Provide/Arrange', 
                            choices=[('None','None'),('Blood', 'Blood'),('Plasma', 'Plasma'),
                            ('Oxygen', 'Oxygen'),('Hospital Bed', 'Hospital Bed'),
                            ('Covid Bed', 'Covid Bed'),('Medicine', 'Medicine'),
                            ('Ambulance', 'Ambulance'), ('Home Care', 'Home Care')],
                            validators=[DataRequired()])
    volunteer = SelectField(u'Do You Want to Volunteer With Us',choices=[('Yes','Yes'),('No','No')])
    feedback = TextAreaField('Tell Us How We Can Improve')
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')			

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')