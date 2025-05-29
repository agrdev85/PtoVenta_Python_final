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
		sender=("CuBaro Email Confirmation", os.environ["EMAIL"]),
		html=html,
	)
	mail.send(msg)


def fulfill_order():
    """Fulfills order on successful payment."""
    uid = session.get('client_reference_id')
    
    if not uid:
        flash("La sesión del usuario expiró o no es válida. Por favor inicia sesión nuevamente.", "error")
        return redirect(url_for('login'))
    
    user = User.query.get(uid)
    if not user or user.id != current_user.id:
        flash("Usuario no encontrado o no autorizado. Por favor inicia sesión nuevamente.", "error")
        return redirect(url_for('login'))
    
    if not user.cart:
        flash("El carrito está vacío.", "error")
        return redirect(url_for('cart'))
    
    order = Order(uid=uid, date=datetime.now(), status="Reservado")
    
    try:
        db.session.add(order)
        db.session.flush()  # Obtener order.id antes de commit
        
        for cart_item in user.cart:
            item = cart_item.item
            if item.stock < cart_item.quantity:
                flash(f"No hay suficiente stock para {item.name}. Solo queda {item.stock} artículo(s).", "error")
                db.session.rollback()
                return redirect(url_for('cart'))
            
            item.stock -= cart_item.quantity
            ordered_item = Ordered_item(oid=order.id, itemid=item.id, quantity=cart_item.quantity)
            db.session.add(ordered_item)
        
        Cart.query.filter_by(uid=uid).delete()
        db.session.commit()
        
        flash("Orden reservada satisfactoriamente!", "success")
        
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error al reservar el producto: {str(e)}")
        flash("Ha ocurrido un error mientras reservaba el producto. Pruebe nuevamente más tarde por favor.", "error")
        return redirect(url_for('cart'))
    
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
		