import os, stripe, json
from flask_bcrypt import Bcrypt  # Ensure Flask-Bcrypt is imported
from datetime import datetime, timedelta, timezone
from flask_wtf import FlaskForm
from flask import Flask, session, render_template, redirect, url_for, flash, request, abort, Response, make_response
from flask_bootstrap import Bootstrap
from wtforms import SelectField
from .forms import ForgotPasswordForm, LoginForm, RegisterForm, EmployeeRegisterForm, ResetPasswordForm, GenerateResetCodeForm
import secrets
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from .extensions import db
from .db_models import Membership, PasswordResetLog, db, User, Item, Alert, Order, Ordered_item
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from .funcs import mail, send_confirmation_email, fulfill_order
from dotenv import load_dotenv
from .admin.routes import admin
from flask_apscheduler import APScheduler 
from markupsafe import Markup
from flask import current_app, json
from weasyprint import HTML
from io import BytesIO
import uuid
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from itsdangerous import URLSafeTimedSerializer



load_dotenv()
app = Flask(__name__, static_folder='static')
bcrypt = Bcrypt(app)  # Initialize Flask-Bcrypt
app.register_blueprint(admin)
""" supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key) """

limiter = Limiter(key_func=get_remote_address, app=app)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,  # Número máximo de conexiones en el pool
    'max_overflow': 20,  # Conexiones extra si el pool está lleno
    'pool_timeout': 30  # Tiempo antes de que una conexión expirada sea reciclada
}

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "123456")
csrf = CSRFProtect(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
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
                message = f"ALERTA: Debe comprar '{item.name}' tiene un stock de {item.stock}, menor o igual al stock mínimo definido en {item.stock_min}."
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


def fix_null_master():
    users = User.query.filter_by(master_key=None).all()
    for user in users:
        if user.admin:
            master_key = secrets.token_urlsafe(16)
            user.master_key = bcrypt.generate_password_hash(master_key).decode('utf-8')
            print(f'Generada master_key para {user.email}: {master_key}')
        else:
            user.master_key = bcrypt.generate_password_hash('TEMP_EMPLOYEE').decode('utf-8')
            print(f'Asignado TEMP_EMPLOYEE para {user.email}')
    db.session.commit()


@app.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    if current_user.id != user_id:
        flash('No tienes permiso para cambiar la contraseña de este usuario.', 'error')
        return redirect(url_for('orders'))

    if current_user.admin:
        flash('Los administradores no necesitan cambiar la contraseña inicial.', 'error')
        return redirect(url_for('admin.dashboard'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        current_user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        current_user.master_key = bcrypt.generate_password_hash('EMPLOYEE_CHANGED').decode('utf-8')
        db.session.commit()
        flash('Contraseña cambiada exitosamente.', 'success')
        return redirect(url_for('orders'))

    return render_template('change_password.html', form=form)


@app.route('/forgot_password', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def forgot_password():
    form = ForgotPasswordForm()
    user = None

    if form.email.data:
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if not user and request.method == 'POST':
            flash('No existe una cuenta con ese correo.', 'error')
            return redirect(url_for('forgot_password'))

    if request.method == 'POST' and form.email.data and not form.master_key.data and not form.reset_code.data:
        if user:
            return render_template('forgot_password.html', form=form, user=user)
        return redirect(url_for('forgot_password'))

    if form.validate_on_submit() and user:
        log = PasswordResetLog(user_id=user.id, success=False)
        db.session.add(log)

        if user.admin:
            master_key = form.master_key.data
            if not master_key or not bcrypt.check_password_hash(user.master_key, master_key):
                flash('Llave maestra incorrecta.', 'error')
                db.session.commit()
                return render_template('forgot_password.html', form=form, user=user)
        else:
            reset_code = form.reset_code.data.strip().lower()  # Normalizar el código ingresado
            if not reset_code:
                flash('Código de recuperación requerido.', 'error')
                db.session.commit()
                return render_template('forgot_password.html', form=form, user=user)

            if not user.master_key:
                flash('No se ha generado un código de recuperación para este usuario.', 'error')
                db.session.commit()
                return render_template('forgot_password.html', form=form, user=user)

            reset_value = f'RESET_{reset_code}'
            print(f"Intentando verificar: reset_code={reset_code}, reset_value={reset_value}, hash={user.master_key}")
            if not bcrypt.check_password_hash(user.master_key, reset_value):
                print(f"Hash no coincide para {reset_value}")
                flash('Código de recuperación inválido.', 'error')
                db.session.commit()
                return render_template('forgot_password.html', form=form, user=user)

            # Expiración basada en la última actualización de master_key
            from sqlalchemy import func
            last_updated = db.session.query(func.max(User.updated_at)).filter_by(id=user.id).scalar()
            if last_updated:
                expiry = last_updated.replace(tzinfo=timezone.utc) + timedelta(hours=1)
                print(f"Last updated: {last_updated}, Expiry: {expiry}, Now: {datetime.now(timezone.utc)}")
                if datetime.now(timezone.utc) > expiry:
                    flash('Código de recuperación expirado.', 'error')
                    db.session.commit()
                    return render_template('forgot_password.html', form=form, user=user)

        token = serializer.dumps(user.email, salt='recover-password')
        log.success = True
        db.session.commit()
        return redirect(url_for('reset_password', token=token))

    return render_template('forgot_password.html', form=form, user=user)

@app.route('/reset_password', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def reset_password():
    token = request.args.get('token') or request.form.get('token')
    if not token:
        flash('Token inválido o faltante.', 'error')
        return redirect(url_for('forgot_password'))

    try:
        email = serializer.loads(token, salt='recover-password', max_age=3600)
    except:
        flash('El enlace ha expirado o no es válido.', 'error')
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Usuario no encontrado.', 'error')
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        if not user.admin:
            user.master_key = bcrypt.generate_password_hash('EMPLOYEE_CHANGED').decode('utf-8')
        db.session.commit()
        flash('Contraseña cambiada exitosamente.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form, token=token)


@app.route('/generate_reset_code', methods=['GET', 'POST'])
@login_required
def generate_reset_code():
    if not current_user.admin:
        flash('Solo los administradores pueden generar códigos de recuperación.', 'error')
        return redirect(url_for('orders'))

    form = GenerateResetCodeForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('No existe una cuenta con ese correo.', 'error')
            return redirect(url_for('generate_reset_code'))

        if user.admin:
            flash('Los administradores deben usar su llave maestra.', 'error')
            return redirect(url_for('generate_reset_code'))

        reset_code = secrets.token_urlsafe(8).lower()  # Código en minúsculas
        reset_value = f'RESET_{reset_code}'  # Solo el reset_code, sin timestamp
        user.master_key = bcrypt.generate_password_hash(reset_value).decode('utf-8')
        db.session.commit()

        print(f"Generado código para {email}: {reset_code}, Master Key: {user.master_key}")
        flash(f'Código de recuperación para {email}: {reset_code}', 'success')
        return redirect(url_for('generate_reset_code'))

    return render_template('generate_reset_code.html', form=form)

@app.route('/confirm_password_reset')
def confirm_password_reset():
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


@app.route('/login', methods=['POST', 'GET'])   
@limiter.limit("15 per hour")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard' if current_user.admin else 'orders'))

    deactivate_expired_users()

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if not user:
            flash(f'El usuario con correo {email} no existe. <a href="{url_for("register_admin")}">Regístrate aquí.</a>', 'error')
            return redirect(url_for('login'))

        if not user.admin and user.creator and not user.creator.email_confirmed:
            flash('Tu administrador está inactivo. No puedes iniciar sesión.', 'error')
            return redirect(url_for('login'))

        if not user.check_membership_status():
            flash('Tu membresía ha vencido. Contacta a Soporte para renovarla.', 'error')
            return redirect(url_for('login'))

        if not user.email_confirmed:
            flash('Debes confirmar tu correo electrónico antes de iniciar sesión. Contacta a Soporte.', 'error')
            return redirect(url_for('login'))

        if bcrypt.check_password_hash(user.password, form.password.data):
            session['client_reference_id'] = user.id
            login_user(user)
            if not user.admin and (user.master_key is None or bcrypt.check_password_hash(user.master_key, 'TEMP_EMPLOYEE')):
                return redirect(url_for('change_password', user_id=user.id))
            return redirect(url_for('admin.dashboard' if user.admin else 'orders'))

        flash('Correo electrónico o contraseña incorrectos.', 'error')

    return render_template('login.html', form=form)


@app.route('/whatsapp', methods=['GET', 'POST'])
def register_admin():
    form = RegisterForm()
    
    # Llenar las opciones del campo membership con (id, nombre)
    memberships = Membership.query.all()
    form.membership.choices = [(m.id, m.name) for m in memberships]
    
    if form.validate_on_submit():
        # Verificar si el correo ya existe
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            link = url_for("login")
            flash(f'El usuario con correo {user.email} ya existe. <a href="{link}">Inicie sesión.</a>', "error")
            return redirect(url_for('login'))
        
        # Determinar el valor de email_confirmed basado en la membresía seleccionada
        if form.membership.data == 1:
            email_confirmed = 1
            membership_expiration = datetime.now(timezone.utc) + timedelta(days=7)
        else:
            email_confirmed = 0
            membership_expiration = datetime.now(timezone.utc)
        
        # Generar una master_key más segura
        master_key = secrets.token_hex(16)  # 16 bytes (32 caracteres)
        
        # Crear el nuevo usuario
        new_user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            password=bcrypt.generate_password_hash(form.password.data).decode('utf-8'),  # Use Flask-Bcrypt
            admin=1,
            email_confirmed=email_confirmed,
            phone=form.phone.data.strip(),
            membership_id=int(form.membership.data),
            membership_expiration=membership_expiration,
            master_key=bcrypt.generate_password_hash(master_key).decode('utf-8')  # Hash the master_key
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            # Pasar la master_key directamente al template
            return render_template("whatsapp.html", form=form, master_key=master_key)
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el administrador.', 'error')
            print(f"Error al registrar administrador: {str(e)}")
            return redirect(url_for('register_admin'))
    
    # Si el formulario no se valida, renderizamos sin master_key
    return render_template("whatsapp.html", form=form, master_key=None)


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.admin != 1:
        flash('No tienes permisos para crear empleados.', 'error')
        return redirect(url_for('admin.configuracion'))

    membership = current_user.membership
    num_empleados = User.query.filter_by(created_by=current_user.id).count()
    if num_empleados >= membership.max_employees:
        flash(f'Solo puedes tener {membership.max_employees} empleados.', 'error')
        return redirect(url_for('admin.configuracion'))

    form = EmployeeRegisterForm()  # Usa el nuevo formulario
    memberships = Membership.query.all()
    if not memberships:
        flash('No hay membresías disponibles. Contacte al soporte.', 'error')
        return redirect(url_for('admin.configuracion'))

    form.membership.choices = [(m.id, m.name) for m in memberships]
    form.membership.data = membership.id  # Membresía del administrador
    form.membership_hidden.data = str(membership.id)

    if form.validate_on_submit():
        print(f"Validación exitosa. Datos: {form.data}")  # Depuración
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash(f'El usuario con correo {form.email.data} ya existe. <a href="{url_for("login")}">Inicie sesión.</a>', 'error')
            return redirect(url_for('register'))

        temp_password = secrets.token_urlsafe(12)  # Contraseña temporal más segura (12 caracteres)
        new_user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            password=bcrypt.generate_password_hash(temp_password).decode('utf-8'),
            admin=0,
            email_confirmed=1,
            created_by=current_user.id,
            phone=form.phone.data.strip(),
            membership_id=int(form.membership_hidden.data),
            membership_expiration=current_user.membership_expiration,
            master_key=bcrypt.generate_password_hash('TEMP_EMPLOYEE').decode('utf-8')  # Hash fijo para empleados
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            print(f"Empleado registrado con éxito. Email: {form.email.data}, Temp Password: {temp_password}")  # Depuración
            return render_template('register.html', form=form, temp_password=temp_password)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el empleado: {str(e)}', 'error')
            print(f"Error al registrar empleado: {str(e)}")  # Depuración
            return redirect(url_for('register'))
    else:
        if form.errors:
            print(f"Validación fallida. Errores: {form.errors}")  # Depuración
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error en {field}: {error}", 'error')

    return render_template('register.html', form=form)

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

@app.route('/add/<int:id>', methods=['GET', 'POST'])
@login_required
def add_to_cart(id):
    if not current_user.is_authenticated:
        flash(f'¡Primero debes iniciar sesión!<br><a href="{url_for("login")}">¡Inicia sesión ahora!</a>', 'error')
        return redirect(url_for('login'))

    item = Item.query.get_or_404(id)
    if request.method == "POST":
        try:
            quantity = int(request.form.get("quantity", 1))
            if quantity < 1 or quantity > item.stock:
                flash(f'Cantidad inválida. Selecciona entre 1 y {item.stock}.', 'error')
                return redirect(url_for('item', id=item.id))
            current_user.add_to_cart(id, quantity)
            flash(f'{item.name} agregado exitosamente al <a href="{url_for("cart")}">carrito</a>.<br><a href="{url_for("cart")}">Ver carrito!</a>', 'success')
            return redirect(url_for('home'))
        except ValueError:
            flash('Cantidad inválida. Por favor, ingresa un número.', 'error')
            return redirect(url_for('item', id=item.id))
    
    # Renderizar la página del artículo para GET
    return render_template('item.html', item=item)

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

@app.route('/fulfill_order', methods=['POST'])
@login_required
def fulfill_order_view():
    if not request.form.get('csrf_token'):
        flash('Token CSRF faltante.', 'error')
        return redirect(url_for('cart'))
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
