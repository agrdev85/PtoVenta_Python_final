from datetime import datetime, timezone
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    phone = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    admin = db.Column(db.Integer, nullable=False, default=0)
    email_confirmed = db.Column(db.Integer, nullable=False, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # ID del creador
    registration_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Fecha de registro
    membership_expiration = db.Column(db.DateTime, nullable=True)  # Fecha de vencimiento de membresía
    employees = db.relationship('User', backref='creator', remote_side=[id], lazy='select')  # Relación empleados
    cart = db.relationship('Cart', backref='buyer')
    orders = db.relationship("Order", backref='customer', foreign_keys="[Order.uid]")  # Relación con clave foránea especificada

    def check_membership_status(self):
      if self.membership_expiration:
        # Convierte fechas naive a UTC antes de comparar
        now = datetime.now(timezone.utc)
        expiration = self.membership_expiration
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=timezone.utc)

        return now <= expiration
      self.email_confirmed = 0
      db.session.commit()
      return False


    def add_to_cart(self, itemid, quantity):
        item_to_add = Cart(itemid=itemid, uid=self.id, quantity=quantity)
        db.session.add(item_to_add)
        db.session.commit()

    def remove_from_cart(self, itemid, quantity):
        item_to_remove = Cart.query.filter_by(itemid=itemid, uid=self.id, quantity=quantity).first()
        db.session.delete(item_to_remove)
        db.session.commit()


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(250), nullable=False)
    details = db.Column(db.String(250), nullable=False)
    price_id = db.Column(db.String(250), nullable=False)
    costo = db.Column(db.Integer)
    stock = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Vincular con el creador
    creator = db.relationship('User', backref='items_created')  # Relación con el usuario que creó el producto
    orders = db.relationship('Ordered_item', backref='item', lazy=True, cascade="all, delete, delete-orphan")
    in_cart = db.relationship("Cart", backref="item", lazy=True, cascade="all, delete, delete-orphan")


class Cart(db.Model):
    __tablename__ = "cart"
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    itemid = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Clave foránea del cliente
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    items = db.relationship("Ordered_item", backref="order", cascade="all, delete-orphan")


class Ordered_item(db.Model):
    __tablename__ = "ordered_items"
    id = db.Column(db.Integer, primary_key=True)
    oid = db.Column(db.Integer, db.ForeignKey('orders.id'))
    itemid = db.Column(db.Integer, db.ForeignKey('items.id'))
    quantity = db.Column(db.Integer, nullable=False)