from flask import Blueprint, jsonify, render_template, session, url_for, flash, request
from flask_login import current_user, login_required
from werkzeug.utils import redirect, secure_filename
from ..db_models import Membership, Order, Ordered_item, Item, db, User
from ..admin.forms import AddItemForm, OrderEditForm
from ..funcs import admin_only
import logging
from sqlalchemy.orm import aliased, joinedload
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta, timezone

admin = Blueprint("admin", __name__, url_prefix="/admin", static_folder="static", template_folder="templates")

@admin.route('/')
@admin_only
def dashboard():
    # Obtener las órdenes relacionadas con el administrador actual o sus empleados
    orders = Order.query.join(User, Order.uid == User.id).filter((User.id == current_user.id) | (User.created_by == current_user.id)
    ).all()

    return render_template("admin/home.html", orders=orders)

@admin.route('/update_order_status/<int:id>', methods=['POST'])
@admin_only
def update_order_status(id):
    # Validar que la orden pertenece al administrador actual o a un empleado del administrador actual
    order = Order.query.join(User, Order.uid == User.id).filter(
        Order.id == id,
        (User.created_by == current_user.id) | (User.id == current_user.id)  # Verificar si es del admin o de un empleado del admin
    ).first_or_404()
    status = request.form.get('status')
    if status in ['Pagado', 'Libre', 'Reservado']:
        order.status = status
        order.date = datetime.now()
        db.session.commit()
        flash(f"¡Estado de la orden actualizado exitosamente a '{status}'!", 'success')
    else:
        flash("¡Estado no válido!", 'error')
    return redirect(url_for('admin.dashboard'))

def create_user_folder(user_id):
    """ Crea una carpeta para el usuario dentro de app/static/upload/ """
    user_folder = f'app/static/upload/{user_id}'
    absolute_folder = os.path.join(os.getcwd(), user_folder)
    
    if not os.path.exists(absolute_folder):
        os.makedirs(absolute_folder)
        print(f"Carpeta creada: {absolute_folder}")
    
    return user_folder    

@admin.route('/items')
@admin_only
def items():
    # Obtener las alertas de la sesión
    alerts = session.pop('alerts', [])
    # Filtrar productos creados por el administrador actual o sus empleados
    items = Item.query.join(User, Item.created_by == User.id).filter(
        (User.id == current_user.id) | (User.created_by == current_user.id)
    ).all()
    return render_template("admin/items.html", items=items, alerts=alerts)

@admin.route('/statictics')
@admin_only
def statictics():
    # Filtrar órdenes relacionadas con el administrador actual o sus empleados
    orders = Order.query.join(User, Order.uid == User.id).filter(
        (User.id == current_user.id) | (User.created_by == current_user.id)
    ).all()
    items = Item.query.join(User, Item.created_by == User.id).filter(
        (User.id == current_user.id) | (User.created_by == current_user.id)
    ).all()
    return render_template("admin/statictics.html", orders=orders, items=items)

def create_user_folder(user_id):
    """
    Crea una carpeta específica para un usuario dentro de 'app/static/uploads'
    """
    user_folder = f'app/static/uploads/{user_id}'
    absolute_folder = os.path.join(os.getcwd(), user_folder)

    if not os.path.exists(absolute_folder):
        os.makedirs(absolute_folder)
        print(f"Carpeta creada: {absolute_folder}")

    return user_folder  # Devuelve la ruta relativa correcta

@admin.route('/add', methods=['POST', 'GET'])
@login_required
@admin_only
def add():
    membership = current_user.membership
    num_items = Item.query.filter_by(created_by=current_user.id).count()

    if num_items >= membership.max_items:
        flash(f"Has alcanzado el límite de {membership.max_items} productos para tu membresía.", 'error')
        return redirect(url_for('admin.dashboard'))

    form = AddItemForm()

    if form.validate_on_submit():
        user_folder = f'static/uploads/{current_user.id}'
        os.makedirs(f'app/{user_folder}', exist_ok=True)  # Crear carpeta si no existe

        image_file = form.image.data
        if image_file:
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(user_folder, filename)  # Ruta dentro de static/
            image_file.save(os.path.join('app', file_path))  # Guardar la imagen en app/static/uploads/
        else:
            file_path = 'static/uploads/default.png'  # Imagen por defecto

        # Crear nuevo item con la ruta de la imagen
        new_item = Item(
            name=form.name.data,
            price=form.price.data,
            category=form.category.data,
            image=f'/{file_path}',  # Guardar en la base de datos con formato correcto
            details=form.details.data,
            costo=form.costo.data,
            stock=form.stock.data,
            stock_min=form.stock_min.data,
            created_by=current_user.id
        )

        db.session.add(new_item)
        try:
            db.session.commit()
            flash(f"¡Artículo '{form.name.data}' agregado exitosamente!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al agregar el artículo: {str(e)}", "error")

        return redirect(url_for('admin.items'))

    return render_template('admin/add.html', form=form)

@admin.route('/edit/item/<int:id>', methods=['POST', 'GET'])
@login_required
@admin_only
def edit(id):
    item = Item.query.filter_by(id=id, created_by=current_user.id).first_or_404()

    form = AddItemForm(
        name=item.name,
        price=item.price,
        category=item.category,
        details=item.details,
        stock_min=item.stock_min,
        costo=item.costo,
        stock=item.stock
    )

    if form.validate_on_submit():
        item.name = form.name.data
        item.price = form.price.data
        item.category = form.category.data
        item.details = form.details.data
        item.stock_min = form.stock_min.data
        item.costo = form.costo.data
        item.stock = form.stock.data

        if form.image.data:
            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            user_folder = f'app/static/uploads/{current_user.id}'
            os.makedirs(user_folder, exist_ok=True)  # Crear carpeta si no existe
            file_path = os.path.join(user_folder, filename)
            image_file.save(file_path)

            # Ajustar la ruta para que sea accesible en la web
            item.image = f'/static/uploads/{current_user.id}/{filename}'

        try:
            db.session.commit()
            flash("¡Artículo actualizado exitosamente!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar el artículo: {str(e)}", "error")

        return redirect(url_for('admin.items'))

    return render_template('admin/add.html', form=form, current_image=item.image)

@admin.route('/delete/<int:id>')
@admin_only
def delete(id):
    to_delete = Item.query.filter_by(id=id, created_by=current_user.id).first()
    if not to_delete:
        flash("No tienes permiso para eliminar este producto.", "error")
        return redirect(url_for('admin.items'))

    if not to_delete.orders:
        db.session.delete(to_delete)
        db.session.commit()
        flash(f"¡Artículo {to_delete.name} eliminado exitosamente!", "success")
    else:
        flash("No se pudo eliminar el artículo porque está relacionado con órdenes.", "error")
    return redirect(url_for('admin.items'))

@admin.route('/delete_order/<int:id>')
@admin_only
def delete_order(id):
    # Validar que la orden pertenece a un empleado del administrador actual
    #order = Order.query.join(User, Order.uid == User.id).filter(Order.id == id, User.created_by == current_user.id).first_or_404()

    # Validar que la orden pertenece al administrador actual o a un empleado del administrador actual
    order = Order.query.join(User, Order.uid == User.id).filter(
        Order.id == id,
        (User.created_by == current_user.id) | (User.id == current_user.id)  # Verificar si es del admin o de un empleado del admin
    ).first_or_404()

    if not order:
        flash("No se encontró la orden.", "error")
        return redirect(url_for('admin.dashboard'))

    if order.status == 'Reservado':
        # Restablecer el stock de los ítems en la orden
        for ordered_item in order.items:
            item = Item.query.get(ordered_item.itemid)
            if item:
                item.stock += ordered_item.quantity

        # Eliminar los ítems asociados a la orden
        Ordered_item.query.filter_by(oid=id).delete()

        # Eliminar la orden
        db.session.delete(order)
        db.session.commit()

        flash("Orden eliminada exitosamente.", "success")
    else:
        flash("No se puede eliminar la orden porque no está en estado 'Reservado'.", "error")

    return redirect(url_for('admin.dashboard'))

# Esta función se ejecutará cada X tiempo para revisar las órdenes pendientes
@admin.route('/update_order_status_to_free', methods=['POST'])
def update_order_status_to_free():
    one_day_ago = datetime.now() - timedelta(days=1)
    
    # Encuentra las órdenes con estado "Pagado" que tienen más de un día
    orders_to_update = Order.query.filter(
        Order.status == 'Pagado',
        Order.date <= one_day_ago
    ).all()

    if orders_to_update:
        for order in orders_to_update:
            order.status = 'Libre'
            db.session.commit()

        flash("El estado del pedido cambió exitosamente a Libre.", "success")
        return redirect(url_for('admin.dashboard'))
    else:
        flash("No hay pedidos para actualizar", "info")
        return redirect(url_for('admin.dashboard'))
    

@admin.route('/configuracion', methods=['GET'])
def configuracion():
    # Crear un alias para referenciar al administrador (creador)
    admin_alias = aliased(User)

    # Consultar todas las membresías disponibles
    memberships = Membership.query.all()

    # Verificar si el usuario actual es el superadmin
    if current_user.id == 1:  # Supongamos que el superadmin tiene ID 1
        # Si es superadmin, mostrar todos los usuarios
        users = db.session.query(
            User,  # El usuario actual
            admin_alias.name.label('creator_name')  # Nombre del creador
        ).outerjoin(
            admin_alias, User.created_by == admin_alias.id  # Relacionar creado_por con ID del administrador
        ).options(joinedload(User.membership)).all()  # Cargar la relación membership
    else:
        # Si es un administrador normal, mostrar solo sus empleados
        users = db.session.query(
            User,
            admin_alias.name.label('creator_name')
        ).outerjoin(
            admin_alias, User.created_by == admin_alias.id
        ).filter(
            User.created_by == current_user.id  # Filtrar solo usuarios creados por el administrador actual
        ).all()

    # Formatear datos para la plantilla
    user_data = [
        {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'admin': user.admin,
            'phone': user.phone,
            'password': user.password,
            'email_confirmed': user.email_confirmed,
            'created_by': user.created_by,
            'registration_date': user.registration_date,
            'membership_expiration': user.membership_expiration,
            'membership_id': user.membership_id,  # Para que se seleccione la membresía en el modal
            'membership': user.membership,  # Incluir la membresía en los datos
            'creator_name': creator_name if creator_name else 'Sin Admin'
        }
        for user, creator_name in users
    ]
    
    # Renderizar plantilla
    return render_template('admin/configuracion.html', users=user_data, memberships=memberships, user=current_user)


@admin.route('/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    try:
        # Obtener el ID de la membresía desde el formulario
        membership_id = request.form.get('membership_id')

        # Obtener la fecha de vencimiento desde el formulario (YYYY-MM-DD)
        membership_expiration_input = request.form.get('membership_expiration')

        # Verificar que la fecha sea válida
        if membership_expiration_input:
            try:
                membership_expiration_date = datetime.strptime(membership_expiration_input, '%Y-%m-%d').date()
                membership_expiration = datetime.combine(membership_expiration_date, datetime.now().time())
            except ValueError:
                flash(f"Fecha de vencimiento inválida.", "error")
        else:
            membership_expiration = None

        # Obtener los demás datos del formulario
        user_name = request.form.get('userName')
        user_email = request.form.get('userEmail')
        user_phone = request.form.get('userPhone')
        password = request.form.get('userPassword')  # Nueva contraseña (opcional)

        # Buscar al usuario en la base de datos
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Usuario no encontrado.'}), 404

        # Verificar permisos según el tipo de usuario actual
        if current_user.id == 1:  # Superadministrador
            user.name = user_name
            user.email = user_email
            user.phone = user_phone
            user.membership_expiration = membership_expiration
            user.membership_id = membership_id  # Asignar la nueva membresía
            user.email_confirmed = request.form.get('email_confirmed', 1)

            # Actualizar contraseña si se proporciona
            if password:
                user.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

            # Actualizar la fecha de vencimiento de los empleados del administrador
            if user.admin:
                User.query.filter(User.created_by == user.id).update(
                    {'membership_id': membership_id, 'membership_expiration': membership_expiration, 'email_confirmed': 1}
                )

        else:  # Administradores normales
            if current_user.admin and user.created_by == current_user.id:
                user.name = user_name
                user.email = user_email
                user.phone = user_phone

                # Actualizar contraseña si se proporciona
                if password:
                    user.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            else:
                return jsonify({'success': False, 'message': 'No tienes permisos para actualizar este usuario.'}), 403

        # Guardar los cambios en la base de datos
        db.session.commit()
        return jsonify({'success': True, 'message': 'Usuario actualizado exitosamente.'})
    
    except Exception as e:
        db.session.rollback()
        logging.error(f'Error al actualizar usuario: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'message': 'Error interno al actualizar el usuario.', 'details': str(e)}), 500
    

@admin.route('/delete_user/<int:id>')
@admin_only
def delete_user(id):
    if id == 1:
        flash("¡El superadministrador no puede ser eliminado!", "error")
        return redirect(url_for('admin.configuracion'))

    user_to_delete = User.query.get(id)

    if not user_to_delete:
        flash("El usuario no existe.", "error")
        return redirect(url_for('admin.configuracion'))

    if current_user.id != 1 and user_to_delete.created_by != current_user.id:
        flash("No tienes permiso para eliminar este usuario.", "error")
        return redirect(url_for('admin.configuracion'))

    # Verificar si el usuario tiene relaciones activas
    if user_to_delete.orders:
        flash("No se puede eliminar el usuario porque tiene órdenes asociadas.", "error")
        return redirect(url_for('admin.configuracion'))

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"¡Usuario {user_to_delete.name} eliminado exitosamente!", "success")
    except Exception as e:
        flash(f"Ocurrió un error al eliminar el usuario: {str(e)}", "error")

    return redirect(url_for('admin.configuracion'))