from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, Optional


class LoginForm(FlaskForm):
	email = StringField("Email", validators=[
        DataRequired(message="El email es requerido."),
        Email(message="Debe ingresar un email válido.")
    ])
	password = PasswordField("Contraseña:", validators=[
        DataRequired(message="La contraseña es requerida."),
        Regexp(regex=r'^[a-zA-Z0-9_\-&$@#!%^*+.]{8,30}$', message='La contraseña debe tener entre 8 y 30 caracteres y contener letras, números y símbolos.')
    ])
	submit = SubmitField("Iniciar Sesión")



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
        Regexp(regex=r'^[a-zA-Z0-9_\-&$@#!%^*+.]{8,30}$', message='La contraseña debe tener entre 8 y 30 caracteres y contener letras, números y símbolos.')
    ])
    
    confirm = PasswordField("Confirma la Contraseña:", validators=[
        DataRequired(message="Debe confirmar la contraseña."),
        EqualTo('password', message='Las contraseñas deben coincidir.')
    ])
    
    submit = SubmitField("Registro")

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
        Regexp(regex=r'^[a-zA-Z0-9_\-&$@#!%^*+.]{8,30}$', message='La contraseña debe tener entre 8 y 30 caracteres y contener letras, números y símbolos.')
    ])
    
    confirm = PasswordField("Confirma la Contraseña:", validators=[
        DataRequired(message="Debe confirmar la contraseña."),
        EqualTo('password', message='Las contraseñas deben coincidir.')
    ])
    
    submit = SubmitField("Registro")

class EmployeeRegisterForm(FlaskForm):
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
    
    submit = SubmitField("Registrar Empleado")   


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(message="El email es requerido."), Email(message="Debe ingresar un email válido.")])
    master_key = StringField("Llave Maestra:", validators=[Optional()])  # Opcional hasta el segundo paso
    reset_code = StringField("Código de Recuperación:", validators=[Optional()])  # Opcional hasta el segundo paso
    submit = SubmitField("Enviar")

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Cambiar Contraseña')

class GenerateResetCodeForm(FlaskForm):
    email = StringField('Correo del Empleado', validators=[DataRequired(), Email()])
    submit = SubmitField('Generar Código')