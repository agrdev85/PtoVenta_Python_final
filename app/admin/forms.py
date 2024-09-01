from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, IntegerField, FileField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange

class AddItemForm(FlaskForm):
    name = StringField("Artículo:", validators=[DataRequired(), Length(max=50)])
    price = FloatField("Precio:", validators=[DataRequired(), NumberRange(min=0, message="El precio debe ser un número positivo.")])
    # Cambiado a SelectField con las opciones especificadas
    category = SelectField("Categoría:", choices=[
        ('Alimentos', 'Alimentos'),
        ('Confituras', 'Confituras'),
        ('Carnicos', 'Cárnicos'),
        ('Bebidas', 'Bebidas'),
        ('Aseo', 'Aseo'),
        ('Miscelaneas', 'Misceláneas')
    ], validators=[DataRequired()])
    image = FileField("Imagen:", validators=[DataRequired()])
    details = StringField("Detalles:", validators=[DataRequired()])
    costo = IntegerField("Costo:", validators=[DataRequired(), NumberRange(min=0, message="El costo debe ser un número positivo.")])
    stock = IntegerField("Stock:", validators=[NumberRange(min=0, message="El stock debe ser un número positivo.")])
    price_id = StringField("Stripe id:", validators=[DataRequired()])
    submit = SubmitField("Guardar")

class OrderEditForm(FlaskForm):
	status = StringField("Estatus:", validators=[DataRequired()])
	submit = SubmitField("Actualizar")
  