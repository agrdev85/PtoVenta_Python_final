from flask import Blueprint, render_template, url_for, flash, request  # Agregamos 'request' aquí
from werkzeug.utils import redirect, secure_filename
from ..db_models import Order, Ordered_item, Item, db, User
from ..admin.forms import AddItemForm, OrderEditForm
from ..funcs import admin_only
import os
from datetime import datetime, timedelta

admin = Blueprint("admin", __name__, url_prefix="/admin", static_folder="static", template_folder="templates")

@admin.route('/')
@admin_only
def dashboard():
    orders = Order.query.all()
        
    return render_template("admin/home.html", orders=orders)

@admin.route('/update_order_status/<int:id>', methods=['POST'])
@admin_only
def update_order_status(id):
    order = Order.query.get_or_404(id)
    status = request.form.get('status')
    if status in ['Pagado', 'Libre', 'Reservado']:
        order.status = status
        order.date = datetime.now()
        db.session.commit()
        flash('¡El estado del pedido se actualizó exitosamente!', 'success')
    else:
        flash('¡Valor de estado no válido!', 'error')
    return redirect(url_for('admin.dashboard'))

@admin.route('/items')
@admin_only
def items():
    items = Item.query.all()
    return render_template("admin/items.html", items=items)

@admin.route('/statictics')
@admin_only
def statictics():
    orders = Order.query.all()
    return render_template("admin/statictics.html", orders = orders)

@admin.route('/add', methods=['POST', 'GET'])
@admin_only
def add():
    form = AddItemForm()
    if form.validate_on_submit():
        image_file = form.image.data
        if image_file:
            image_file.save('app/static/uploads/' + image_file.filename)
            image_file = url_for('static', filename=f'uploads/{image_file.filename}')
        else:
            image_file = None  # O maneja un valor por defecto si no se sube imagen

        # Asignar la imagen predeterminada de agotado si el stock es cero o menor
        if form.stock.data <= 0:
            image_file = url_for('static', filename='uploads/agotado.png')

        new_item = Item(
            name=form.name.data,
            price=form.price.data,
            category=form.category.data,
            image=image_file,
            details=form.details.data,
            costo=form.costo.data,
            stock=form.stock.data,
            price_id=form.price_id.data
        )
        db.session.add(new_item)
        try:
            db.session.commit()
            flash("¡Artículo agregado exitosamente!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")
        return redirect(url_for('admin.items'))
    return render_template('admin/add.html', form=form)

@admin.route('/edit/<string:type>/<int:id>', methods=['POST', 'GET'])
@admin_only
def edit(type, id):
    if type == "item":
        item = Item.query.get(id)
        form = AddItemForm(
            name=item.name,
            price=item.price,
            category=item.category,
            details=item.details,
            image=item.image,
            price_id=item.price_id,
            costo=item.costo,
            stock=item.stock
        )
        if form.validate_on_submit():
            item.name = form.name.data
            item.price = form.price.data
            item.category = form.category.data
            item.details = form.details.data
            item.price_id = form.price_id.data
            item.costo = form.costo.data
            item.stock = form.stock.data

            # Si se sube una nueva imagen, la guardamos y actualizamos el valor de item.image
            if form.image.data:
                form.image.data.save('app/static/uploads/' + form.image.data.filename)
                item.image = url_for('static', filename=f'uploads/{form.image.data.filename}')
        
            db.session.commit()
            flash("¡Artículo actualizado exitosamente!", "success")
            return redirect(url_for('admin.items'))

    elif type == "order":
        order = Order.query.get(id)
        form = OrderEditForm(status=order.status)
        if form.validate_on_submit():
            order.status = form.status.data
            db.session.commit()
            flash("¡Pedido actualizado exitosamente!", "success")
            return redirect(url_for('admin.dashboard'))

    return render_template('admin/add.html', form=form)

@admin.route('/delete/<int:id>')
@admin_only
def delete(id):
    to_delete = Item.query.get(id)
    if to_delete is None:
        flash("Artículo no encontrado.", "error")
        return redirect(url_for('admin.items')) 

    if not to_delete.ordered_items:
        db.session.delete(to_delete)
        db.session.commit()
        flash("¡Artículo eliminado exitosamente!", "success")
    else:
        flash("No se pudo eliminar el elemento. Es posible que tenga artículos pedidos relacionados.", "error")

    return redirect(url_for('admin.items'))

@admin.route('/delete_order/<int:id>')
@admin_only
def delete_order(id):
    # Obtener la orden por ID
    order = Order.query.get(id)
    
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

        jsonify({"message": "Estados de pedidos actualizados a 'Libre'"}), 200
        flash("El estado del pedido cambió exitosamente a Libre.", "success")
        return redirect(url_for('admin.dashboard'))
    else:
        jsonify({"message": "No hay pedidos para actualizar"}), 200