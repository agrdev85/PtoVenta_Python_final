from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, IntegerField, FileField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.file import FileAllowed

class AddItemForm(FlaskForm):
    name = StringField("Artículo:", validators=[DataRequired(), Length(max=50)])
    price = FloatField("Precio:", validators=[DataRequired(), NumberRange(min=0, message="El precio debe ser un número positivo.")])
    category = SelectField("Categoría:", choices=[
        ('Alimentos', 'Alimentos'),
        ('Confituras', 'Confituras'),
        ('Carnicos', 'Cárnicos'),
        ('Bebidas', 'Bebidas'),
        ('Aseo', 'Aseo'),
        ('Miscelaneas', 'Misceláneas')
    ], validators=[DataRequired()])
    image = FileField("Imagen:", validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], "Solo se permiten imágenes")
    ])  # Eliminado DataRequired para hacerlo opcional
    details = StringField("Detalles:", validators=[DataRequired()])
    costo = IntegerField("Costo:", validators=[DataRequired(), NumberRange(min=0, message="El costo debe ser un número positivo.")])
    stock = IntegerField("Stock:", validators=[NumberRange(min=0, message="El stock debe ser un número positivo.")])
    stock_min = IntegerField("Stock Min:", validators=[NumberRange(min=0, message="El stock minimo debe ser un número positivo.")])
    submit = SubmitField("Guardar", render_kw={"class": "btn btn-success mr-4"}) # Cambia la clase CSS del botón aquí

class OrderEditForm(FlaskForm):
	status = StringField("Estatus:", validators=[DataRequired()])
	submit = SubmitField("Actualizar")
  