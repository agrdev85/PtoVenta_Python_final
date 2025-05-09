import os, stripe, json
from datetime import datetime, timedelta, timezone
from flask_wtf import FlaskForm
from flask import Flask, session, render_template, redirect, url_for, flash, request, abort, Response, make_response
from flask_bootstrap import Bootstrap
from .forms import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from .extensions import db
from .db_models import Membership, db, User, Item, Alert, Order, Ordered_item
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from .funcs import mail, send_confirmation_email, fulfill_order
from supabase import create_client, Client
from dotenv import load_dotenv
from .admin.routes import admin
from flask_apscheduler import APScheduler 
from markupsafe import Markup
from flask import current_app, json
from weasyprint import HTML
from io import BytesIO

load_dotenv()
app = Flask(__name__, static_folder='static')
app.register_blueprint(admin)
""" supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key) """

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,  # Número máximo de conexiones en el pool
    'max_overflow': 20,  # Conexiones extra si el pool está lleno
    'pool_timeout': 30  # Tiempo antes de que una conexión expirada sea reciclada
}

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "123456")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local_db.sqlite3'
#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///local_db.sqlite3")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_USERNAME'] = os.environ.get("EMAIL", "agr@gmail.com")
app.config['MAIL_PASSWORD'] = os.environ.get("PASSWORD", "root")
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_PORT'] = 587
app.config['WTF_CSRF_ENABLED'] = True  # Asegúrate de que esté habilitado
stripe.api_key = os.environ.get("STRIPE_PRIVATE", "123456")
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Configuración de la clase para APScheduler
class Config:
    SCHEDULER_API_ENABLED = True


# Instancia de APScheduler
scheduler = APScheduler()

# Función para desactivar usuarios con membresías vencidas
def deactivate_expired_users():
    now = datetime.now(timezone.utc)
    try:
        # Excluir al superadmin con id=1
        expired_users = User.query.filter(
            User.id != 1,  # Excluir al superadmin
            User.membership_expiration < now,
            User.email_confirmed == 1
        ).all()

        for user in expired_users:
            user.email_confirmed = 0
            app.logger.info(f"Usuario {user.id} desactivado por membresía vencida.")

        db.session.commit()
    except Exception as e:
        app.logger.error(f"Error al desactivar usuarios con membresías vencidas: {e}")

# Función para verificar el stock y actualizar alertas
def check_stock():
    with app.app_context():
        items = Item.query.all()

        for item in items:
            if item.stock_min is not None and item.stock <= item.stock_min:
                # Eliminar cualquier alerta existente para este producto
                Alert.query.filter(
                    Alert.message.contains(f"'{item.name}'"),
                    Alert.user_id == item.created_by
                ).delete()

                # Crear una nueva alerta actualizada
                message = f"ALERTA: El producto '{item.name}' tiene un stock de {item.stock}, que es menor o igual al stock mínimo de {item.stock_min}."
                nueva_alerta = Alert(
                    message=message,
                    category='warning',
                    user_id=item.created_by
                )
                db.session.add(nueva_alerta)

        db.session.commit()

def clean_old_alerts():
    with app.app_context():
        # Eliminar alertas con más de 7 días
        old_alerts = Alert.query.filter(Alert.created_at < datetime.now(timezone.utc) - timedelta(days=7)).all()
        for alert in old_alerts:
            db.session.delete(alert)
        db.session.commit()                

Bootstrap(app)
db.init_app(app)
mail.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Inicializar el programador
scheduler.init_app(app)
scheduler.start()

# Agregar la tarea deactivate_expired_users al programador
scheduler.add_job(
        id='deactivate_expired_users',
        func=deactivate_expired_users,
        trigger='interval',
        hours=24
    ) 

# Agregar la tarea clean_old_alerts al programador
scheduler.add_job(
    id='clean_old_alerts',
    func=clean_old_alerts,
    trigger='interval',
    days=1  # Ejecutar diariamente
)  

# Agregar la tarea check_stock al programador
scheduler.add_job(
    id='check_stock',
    func=check_stock,
    trigger='interval',
    minutes=1
)

with app.app_context():
	db.create_all()

@app.context_processor
def inject_now():
	""" sends datetime to templates as 'now' """
	return {'now': datetime.now(timezone.utc)}

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            # Verificar si es administrador
            if user.admin != 1:
                flash("Solo los administradores pueden restablecer su contraseña.", "error")
                return redirect(url_for('login'))

            # Si es admin, generar el token y mostrar el enlace
            token = serializer.dumps(email, salt='recover-password')
            link = url_for('reset_password', token=token, _external=True)

            # ⚠️ Mostrar enlace directamente (ya que no se envía por correo)
            flash(f"{link}", "info")
        else:
            flash("Correo no encontrado.", "error")

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='recover-password', max_age=3600)
    except:
        flash("El enlace ha expirado o es inválido.", "error")
        return redirect(url_for('forgot_password'))

    # Buscar usuario antes de procesar formulario
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form['password']
        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "error")
            return render_template('reset_password.html', token=token)

        user.password = generate_password_hash(password)
        db.session.commit()
        flash("Contraseña actualizada correctamente.", "success")
        return redirect(url_for('confirm_password_reset', token=token))

    return render_template('reset_password.html', token=token)

@app.route('/confirm_password_reset/<token>')
def confirm_password_reset(token):
    try:
        email = serializer.loads(token, salt='recover-password', max_age=3600)
    except:
        flash("El enlace ha expirado.", "error")
        return redirect(url_for('login'))

    return render_template('confirm_password_reset.html')

@app.route("/export_order/<int:order_id>")
def export_order(order_id):
    order = Order.query.get_or_404(order_id)

    # Obtener datos enviados desde SweetAlert o un formulario
    cliente = request.args.get("cliente", "Cliente Desconocido")
    ci = request.args.get("ci", "N/A")
    direccion_cliente = request.args.get("direccion_cliente", "No especificada")
    emitido_por = request.args.get("emitido_por", "Sistema")
    direccion_negocio = request.args.get("direccion_negocio", "No especificada")

    # Nuevos datos dinámicos del negocio desde el formulario
    nombre_negocio = request.args.get("nombre_negocio", "Mi Negocio")
    nit = request.args.get("nit", "000000000")
    telefono = request.args.get("telefono", "000-0000")
    email = request.args.get("email", "sin-email@ejemplo.com")

    # Renderizar HTML con los datos
    html = render_template("order_pdf.html",
                           order=order,
                           cliente=cliente,
                           ci=ci,
                           direccion_cliente=direccion_cliente,
                           emitido_por=emitido_por,
                           direccion_negocio=direccion_negocio,
                           nombre_negocio=nombre_negocio,
                           nit=nit,
                           telefono=telefono,
                           email=email)

    # Convertir HTML a PDF
    pdf_io = BytesIO()
    HTML(string=html).write_pdf(pdf_io)
    pdf_io.seek(0)

    # Crear y devolver el PDF como respuesta
    response = make_response(pdf_io.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=orden_{order.id}.pdf'
    return response

@app.route("/")
def home():
    # Verifica si el usuario está autenticado
    if current_user.is_authenticated:
        # Si el usuario está autenticado, revisamos si tiene membresía activa
        if not current_user.check_membership_status():
            # Si no tiene una membresía activa, redirige a la página de membresía
            return redirect(url_for('membership_plans'))  # Página de planes de membresía
        else:
            # Si tiene membresía, mostrar los productos
            if current_user.admin:
                items = Item.query.filter(Item.created_by == current_user.id).all()
            else:
                items = Item.query.filter(Item.created_by == current_user.created_by).all()
            return render_template("home.html", items=items)
    else:
        # Si no está autenticado, lo redirigimos a la página de login
        return redirect(url_for('membership_plans'))
    
@app.route("/membership_plans")
def membership_plans():
    return render_template("membership_plans.html")


@app.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    deactivate_expired_users()  # Verificar membresías expiradas

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user is None:
            flash(f'El usuario con correo electrónico {email} no existe. <a href={url_for("register_admin")}>Regístrese aquí.</a>', 'error')
            return redirect(url_for('login'))

        # Verificar si el administrador está activo (para empleados)
        if not user.admin and user.creator and not user.creator.email_confirmed:
            flash('Su administrador está inactivo. No puede iniciar sesión.', 'error')
            return redirect(url_for('login'))
        
        # Verificar estado de membresía
        if not user.check_membership_status():
            flash('Su membresía ha vencido. Contacte a Soporte para renovarla.', 'error')
            return redirect(url_for('login'))

        # Verificar si el correo electrónico está confirmado
        if not user.email_confirmed:
            flash('Debe confirmar su correo electrónico antes de iniciar sesión. Contacte a Soporte', 'error')
            return redirect(url_for('login'))


        # Verificar la contraseña
        if check_password_hash(user.password, form.password.data):
            session['client_reference_id'] = user.id
            login_user(user)
            return redirect(url_for('home'))

        flash("Correo electrónico o contraseña incorrectos.", "error")
    return render_template("login.html", form=form)

@app.route('/whatsapp', methods=['GET', 'POST'])
def register_admin():
    form = RegisterForm()
    
    # Llenar las opciones del campo membership con (id, nombre)
    memberships = Membership.query.all()
    form.membership.choices = [(m.id, m.name) for m in memberships]  # (id, nombre)
    
    if form.validate_on_submit():
        # Verificar si el correo ya existe
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash(f"El usuario con correo {user.email} ya existe. <a href={url_for('login')}>Inicie sesión.</a>", "error")
            return redirect(url_for('register_admin'))
        
        # Determinar el valor de email_confirmed basado en la membresía seleccionada
        if form.membership.data == 1:  # Si la membresía seleccionada es "Prueba"
            email_confirmed = 1
            membership_expiration=datetime.now(timezone.utc) + timedelta(days=7)  # 7 días de prueba
        else:  # Para otras membresías, email_confirmed será 0
            email_confirmed = 0
            membership_expiration = datetime.now(timezone.utc)  # No tiene expiración para otras membresías (o poner None si no aplica)
        
        # Crear el nuevo usuario
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
            admin=1,  # Marca como administrador
            email_confirmed=email_confirmed,  # Establecer según la membresía
            phone=form.phone.data,
            membership_id=form.membership.data,  # Guardar el ID de la membresía seleccionada
            membership_expiration=membership_expiration  # Asignar la fecha de expiración (si aplica)
        )
        
        # Guardar el nuevo usuario en la base de datos
        db.session.add(new_user)
        db.session.commit()
        
        flash('¡Registro exitoso! Puede iniciar sesión ahora.', 'success')
        return redirect(url_for('login'))
    
    return render_template("whatsapp.html", form=form)


@app.route("/register", methods=['POST', 'GET'])  # Registrar Empleados
def register():
    # Verifica si el usuario está autenticado antes de acceder al atributo 'admin'
    if current_user.admin != 1:
        flash('No tienes permisos para crear empleados.', 'error')
        return redirect(url_for('admin.dashboard'))

    # Obtén el tipo de membresía del administrador (creador)
    membership = current_user.membership
    numEmpleados = User.query.filter_by(created_by=current_user.id).count()

    if numEmpleados >= membership.max_employees:
        flash(f"Solo puedes tener {membership.max_employees} empleados.", 'error')
        return redirect(url_for('admin.dashboard'))

    form = RegisterForm()

    # Verificar las opciones de membresía
    print("Opciones de membresía disponibles:")
    for m in Membership.query.all():
        print(f"ID: {m.id}, Name: {m.name}")

    # Asignar el valor de la membresía al formulario
    form.membership.choices = [(m.id, m.name) for m in Membership.query.all()]
    # Depuración
    print(f"Opciones disponibles en form.membership.choices: {form.membership.choices}")

    # Establecer el valor predeterminado de la membresía
    form.membership.data = int(membership.id)  # Asegurarte de que es un valor entero
    print(f"Valor de form.membership.data antes de la validación: {form.membership.data}")

    if form.membership.data not in [x[0] for x in form.membership.choices]:
       print(f"Error: El valor {form.membership.data} no está en las opciones")

    form.membership_hidden.data = form.membership.data 
    # Verificar si el valor asignado a 'membership.data' existe en las opciones
    print(f"ID asignado a membership.data: {form.membership.data}")
    # Depuración para ver qué valor se está recibiendo en la solicitud POST
    print(f"Valor de membership en el formulario: {form.membership.data}")
    print(f"Valor de membership_hidden en el formulario: {form.membership_hidden.data}")
    print(f"Tipo de form.membership.data: {type(form.membership.data)}")


    print("Formulario recibido, validando...")
    print(f"Errores del formulario: {form.errors}")
    print(f"Tipo de solicitud: {request.method}")

    if form.validate_on_submit():
        # Depuración
        print(f"Valor de membership_hidden recibido: {form.membership_hidden.data}")
        print(f"Formulario validado correctamente")
        print(f"Nombre: {form.name.data}")
        print(f"Correo: {form.email.data}")
        print(f"Membresía seleccionada: {form.membership.data}")
        print(f"Errores del formulario: {form.errors}")

        # Verificar si el correo ya existe
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash(f"El usuario con correo {user.email} ya existe. <a href={url_for('login')}>Inicie sesión.</a>", "error")
            return redirect(url_for('register'))
        
        # Depuración
        print("Formulario validado correctamente")

        # Crear el nuevo usuario con la membresía del administrador (usando el 'id' de la membresía)
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
            admin=0,  # Usuario normal
            email_confirmed=1,  # Activo automáticamente
            created_by=current_user.id,
            phone=form.phone.data,
            membership_id=form.membership_hidden.data,  # Guardamos el 'id' de la membresía
            membership_expiration=current_user.membership_expiration  # Vence con el administrador
        )

        # Guardar el nuevo usuario en la base de datos
        db.session.add(new_user)
        db.session.commit()

        flash('Empleado creado exitosamente.', 'success')
        return redirect(url_for('admin.dashboard'))

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
	items = []
	quantity = []
	for cart in current_user.cart:
		items.append(cart.item)
		quantity.append(cart.quantity)
		price_id_dict = {
			"price": cart.item.price,
			"quantity": cart.quantity,
			}
		price += cart.item.price*cart.quantity
		redirect(url_for('cart'))
	return render_template('cart.html', items=items, price=price, quantity=quantity)

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

    # Verifica si el usuario actual es un Administrador o un Empleado
    if current_user.admin == 1:  # Si es un Administrador
        # El administrador ve los productos que ha creado él mismo
        items = Item.query.filter(Item.created_by == current_user.id).filter(Item.name.like(search)).all()
    else:
        # Si es un Empleado, ve los productos creados por el Administrador
        items = Item.query.filter(Item.created_by == current_user.created_by).filter(Item.name.like(search)).all()

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
	data = json.loads(request.form['price_id_dict'].replace("'", '"'))
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
