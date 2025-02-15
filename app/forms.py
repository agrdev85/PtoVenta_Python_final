from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp


class LoginForm(FlaskForm):
	email = StringField("Email", validators=[DataRequired()])
	password = PasswordField("Contraseña", validators=[DataRequired()])
	submit = SubmitField("Acceder")

class RegisterForm(FlaskForm):
    name = StringField("Nombre:", validators=[DataRequired(), Length(max=50)])
    phone = StringField("Movil:", validators=[DataRequired(), Length(max=30)])
    membership = SelectField("Membresía:", choices=[('trial', 'Prueba'), ('basic', 'Básica'), ('premium', 'Profesional')], validators=[DataRequired()])
    email = StringField("Email:", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña:", validators=[DataRequired(), Regexp("^[a-zA-Z0-9_\-&$@#!%^*+.]{8,30}$", message='La contraseña debe tener 8 caracteres y debe contener letras, números y símbolos.')])
    confirm = PasswordField("Confirma la Contraseña:", validators=[EqualTo('password', message='Las contraseñas deben coincidir')])
    submit = SubmitField("Registro")