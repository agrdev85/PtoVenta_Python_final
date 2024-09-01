import os, stripe, json
from datetime import datetime, timedelta
from flask import Flask, session, render_template, redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from .forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from .db_models import db, User, Item, Order, Ordered_item
from itsdangerous import URLSafeTimedSerializer
from .funcs import mail, send_confirmation_email, fulfill_order
from dotenv import load_dotenv
from .admin.routes import admin
from flask_apscheduler import APScheduler
from markupsafe import Markup
from flask import current_app, json


load_dotenv()
app = Flask(__name__)
app.register_blueprint(admin)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "123456")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///test.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_USERNAME'] = os.environ.get("EMAIL", "agr@gmail.com")
app.config['MAIL_PASSWORD'] = os.environ.get("PASSWORD", "root")
app.config['MAIL_SERVER'] = "smtp.googlemail.com"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_PORT'] = 587
stripe.api_key = os.environ.get("STRIPE_PRIVATE", "123456")

Bootstrap(app)
db.init_app(app)
mail.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

with app.app_context():
	db.create_all()

@app.context_processor
def inject_now():
	""" sends datetime to templates as 'now' """
	return {'now': datetime.utcnow()}

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)

@app.route("/")
def home():
	items = Item.query.all()
	return render_template("home.html", items=items)

@app.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        
        if user is None:
            flash(f'¡El usuario con correo electrónico {email} no existe!<br> <a href={url_for("register")}>¡Regístrese ahora!</a>', 'error')
            return redirect(url_for('login'))
        
        elif check_password_hash(user.password, form.password.data):
            # Establece la ID del usuario en la sesión
            session['client_reference_id'] = user.id
            login_user(user)
            return redirect(url_for('home'))
        
        else:
            flash("Correo electrónico y contraseña incorrectos!!", "error")
            return redirect(url_for('login'))
    
    return render_template("login.html", form=form)


@app.route("/register", methods=['POST', 'GET'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegisterForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			flash(f"El usuario con correo electrónico {user.email} ya existe!!<br> <a href={url_for('login')}>¡Inicia sesión ahora!</a>", "error")
			return redirect(url_for('register'))
		new_user = User(name=form.name.data,
						email=form.email.data,
						password=generate_password_hash(
									form.password.data,
									method='pbkdf2:sha256',
									salt_length=8),
						phone=form.phone.data)
		db.session.add(new_user)
		db.session.commit()
		# send_confirmation_email(new_user.email)
		flash('¡Gracias por registrarte! Puede iniciar sesión ahora.', 'success')
		return redirect(url_for('login'))
	return render_template("register.html", form=form)

@app.route('/confirm/<token>')
def confirm_email(token):
	try:
		confirm_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
		email = confirm_serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
	except:
		flash('El enlace de confirmación no es válido o ha caducado.', 'error')
		return redirect(url_for('login'))
	user = User.query.filter_by(email=email).first()
	if user.email_confirmed:
		flash(f'Cuenta ya confirmada. Por favor inicie sesión.', 'success')
	else:
		user.email_confirmed = True
		db.session.add(user)
		db.session.commit()
		flash('¡Dirección de correo electrónico confirmada exitosamente!', 'success')
	return redirect(url_for('login'))

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route("/resend")
@login_required
def resend():
	send_confirmation_email(current_user.email)
	logout_user()
	flash('Correo electrónico de confirmación enviado exitosamente.', 'success')
	return redirect(url_for('login'))

@app.route("/add/<id>", methods=['POST'])
def add_to_cart(id):
	if not current_user.is_authenticated:
		flash(f'¡Primero debes iniciar sesión!<br> <a href={url_for("login")}>¡Inicia sesión ahora!</a>', 'error')
		return redirect(url_for('login'))

	item = Item.query.get(id)
	if request.method == "POST":
		quantity = request.form["quantity"]
		current_user.add_to_cart(id, quantity)
		flash(f'''{item.name} agregado exitosamente al <a href=cart>carrito</a>.<br> <a href={url_for("cart")}>ver carrito!</a>''','success')
		return redirect(url_for('home'))

@app.route("/cart")
@login_required
def cart():
	price = 0
	price_ids = []
	items = []
	quantity = []
	for cart in current_user.cart:
		items.append(cart.item)
		quantity.append(cart.quantity)
		price_id_dict = {
			"price": cart.item.price_id,
			"quantity": cart.quantity,
			}
		price_ids.append(price_id_dict)
		price += cart.item.price*cart.quantity
	return render_template('cart.html', items=items, price=price, price_ids=price_ids, quantity=quantity)

@app.route('/orders')
@login_required
def orders():
	return render_template('orders.html', orders=current_user.orders)

@app.route("/fulfill_order", methods=['POST'])
def fulfill_order_view():
    return fulfill_order()

@app.route("/remove/<id>/<quantity>")
@login_required
def remove(id, quantity):
	current_user.remove_from_cart(id, quantity)
	return redirect(url_for('cart'))

@app.route('/item/<int:id>')
def item(id):
	item = Item.query.get(id)
	return render_template('item.html', item=item)

@app.route('/search')
def search():
    query = request.args.get('query', '')
    search = f"%{query}%"
    items = Item.query.filter(Item.name.like(search)).all()

    # Renderiza solo el fragmento HTML con los resultados
    return render_template('search_results.html', items=items)

# stripe stuffs
@app.route('/payment_success')
def payment_success():
	return render_template('success.html')

@app.route('/payment_failure')
def payment_failure():
	return render_template('failure.html')

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
	data = json.loads(request.form['price_ids'].replace("'", '"'))
	try:
		checkout_session = stripe.checkout.Session.create(
			client_reference_id=current_user.id,
			line_items=data,
			payment_method_types=[
			  'card',
			],
			mode='payment',
			success_url=url_for('payment_success', _external=True),
			cancel_url=url_for('payment_failure', _external=True),
		)
	except Exception as e:
		return str(e)
	return redirect(checkout_session.url, code=303)

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():

	if request.content_length > 1024*1024:
		print("Request too big!")
		abort(400)

	payload = request.get_data()
	sig_header = request.environ.get('HTTP_STRIPE_SIGNATURE')
	ENDPOINT_SECRET = os.environ.get('ENDPOINT_SECRET')
	event = None

	try:
		event = stripe.Webhook.construct_event(
		payload, sig_header, ENDPOINT_SECRET
		)
	except ValueError as e:
		# Invalid payload
		return {}, 400
	except stripe.error.SignatureVerificationError as e:
		# Invalid signature
		return {}, 400

	if event['type'] == 'checkout.session.completed':
		session = event['data']['object']

		# Fulfill the purchase...
		fulfill_order(session)

	# Passed signature verification
	return {}, 200
