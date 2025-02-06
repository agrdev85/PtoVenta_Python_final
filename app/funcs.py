import os
from datetime import datetime  # Asegúrate de importar datetime de esta manera
from sqlalchemy.exc import SQLAlchemyError  # Asegúrate de importar SQLAlchemyError
from flask import session, redirect, render_template, flash, url_for
from itsdangerous import URLSafeTimedSerializer
from flask_login import current_user
from flask_mail import Mail, Message
from dotenv import load_dotenv
from .db_models import Order, Ordered_item, db, User, Cart


load_dotenv()
mail = Mail()

def send_confirmation_email(user_email) -> None:
	""" sends confirmation email """
	confirm_serializer = URLSafeTimedSerializer(os.environ["SECRET_KEY"])
	confirm_url = url_for(
						'confirm_email',
						token=confirm_serializer.dumps(user_email,
						salt='email-confirmation-salt'),
						_external=True)
	html = render_template('email_confirmation.html', confirm_url=confirm_url)
	msg = Message(
		'Confirm Your Email Address',
		recipients=[user_email],
		sender=("LUDOC-shop Email Confirmation", os.environ["EMAIL"]),
		html=html,
	)
	mail.send(msg)

def fulfill_order():
    """Fulfills order on successful payment."""
    uid = session.get('client_reference_id')
    
    if not uid:
        flash("La sesión del usuario expiró o no es válida. Por favor inicia sesión nuevamente.", "error")
        return redirect(url_for('login'))  # Redirigir al login si no hay uid en la sesión
    
    current_user = User.query.get(uid)
    if not current_user:
        flash("Usuario no encontrado. Por favor inicia sesión nuevamente.", "error")
        return redirect(url_for('login'))  # Redirigir al login si el usuario no existe
    
    order = Order(uid=uid, date=datetime.now(), status="Reservado")
    
    try:
        # Añadir la orden a la base de datos
        db.session.add(order)
        
        # Procesar el carrito de compras del usuario
        for cart_item in current_user.cart:
            item = cart_item.item  # Obtener el artículo asociado al carrito
            # Verificar si hay stock disponible
            if item.stock < cart_item.quantity:
                flash(f"No hay suficiente stock para {item.name}. Solo queda {item.stock} artículo(s).", "error")
                # No continuamos procesando este artículo en caso de falta de stock
                continue

            # Reducir el stock disponible
            item.stock -= cart_item.quantity

            # Crear el artículo ordenado
            ordered_item = Ordered_item(oid=order.id, itemid=item.id, quantity=cart_item.quantity)
            db.session.add(ordered_item)

        # Eliminar todos los artículos del carrito
        Cart.query.filter_by(uid=uid).delete()

        # Confirmar todos los cambios en la base de datos
        db.session.commit()

        flash("Orden reservada satisfactoriamente!", "success")

    except SQLAlchemyError as e:
        db.session.rollback()
        # Imprimir el error de SQLAlchemy para depuración
        print(f"Error al reservar el producto: {str(e)}")
        flash("Ha ocurrido un error mientras reservaba el producto. Pruebe nuevamente más tarde por favor.", "error")

    # Redirigir a la página de pedidos
    orders = Order.query.filter_by(uid=uid).all()
    return redirect(url_for('orders'))

def admin_only(func):
	""" Decorator for giving access to authorized users only """
	def wrapper(*args, **kwargs):
		if current_user.is_authenticated and current_user.admin == 1:
			return func(*args, **kwargs)
		else:
			return "No estás autorizado a acceder a esta URL."
	wrapper.__name__ = func.__name__
	return wrapper
		