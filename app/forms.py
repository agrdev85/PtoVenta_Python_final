from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp


class LoginForm(FlaskForm):
	email = StringField("Email", validators=[DataRequired()])
	password = PasswordField("Contraseña", validators=[DataRequired()])
	submit = SubmitField("Acceder")

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo

class RegisterForm(FlaskForm):
    name = StringField("Nombre:", validators=[
        DataRequired(message="El nombre es requerido."),
        Length(max=12, message="El nombre no puede tener más de 12 caracteres.")
    ])
    
    phone = StringField("Movil:", validators=[
        DataRequired(message="El teléfono es requerido."),
        Regexp(regex=r'^\d{8}$', message="El teléfono debe tener exactamente 8 dígitos.")
    ])
    
    membership = SelectField('Membresía', coerce=int, validators=[DataRequired(message="La membresía es requerida.")])
    membership_hidden = HiddenField("Membresía (oculta)")  # Campo oculto para almacenar membership
    
    email = StringField("Email:", validators=[
        DataRequired(message="El email es requerido."),
        Email(message="Debe ingresar un email válido.")
    ])
    
    password = PasswordField("Contraseña:", validators=[
        DataRequired(message="La contraseña es requerida."),
        Regexp(regex=r'^[a-zA-Z0-9_\-&$@#!%^*+.]{8,30}$', message='La contraseña debe tener entre 8 y 30 caracteres y puede contener letras, números y símbolos.')
    ])
    
    confirm = PasswordField("Confirma la Contraseña:", validators=[
        DataRequired(message="Debe confirmar la contraseña."),
        EqualTo('password', message='Las contraseñas deben coincidir.')
    ])
    
    submit = SubmitField("Registro")