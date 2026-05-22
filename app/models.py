from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# ── Tabla intermedia (muchos a muchos) ──────────────────────────────────────
# No es un modelo completo, es solo una tabla de asociación.
# SQLAlchemy la maneja sola, no necesitás crear una clase para esto.
product_categories = db.Table('product_categories',
    db.Column('producto_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('categoria_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

# ── Categorías ───────────────────────────────────────────────────────────────
class Category(db.Model):
    __tablename__ = 'categories'

    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(100), nullable=False)
    slug     = db.Column(db.String(100), unique=True, nullable=False)
    icono    = db.Column(db.String(50))   # nombre del ícono, ej: "spray"
    activa   = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Category {self.nombre}>'

# ── Productos ────────────────────────────────────────────────────────────────
class Product(db.Model):
    __tablename__ = 'products'

    id                 = db.Column(db.Integer, primary_key=True)
    nombre             = db.Column(db.String(200), nullable=False)
    descripcion        = db.Column(db.Text)
    imagen_url         = db.Column(db.String(500))
    precio_unidad      = db.Column(db.Numeric(10, 2), nullable=False)
    precio_mayor       = db.Column(db.Numeric(10, 2))
    precio_caja        = db.Column(db.Numeric(10, 2))
    cantidad_mayor     = db.Column(db.Integer)  # cantidad mínima para precio mayor
    unidades_por_caja  = db.Column(db.Integer)
    stock              = db.Column(db.Integer, default=0, nullable=False)
    stock_minimo       = db.Column(db.Integer, default=5)  # dispara alerta
    tiene_variantes    = db.Column(db.Boolean, default=False)
    activo             = db.Column(db.Boolean, default=True)

    # Relación muchos a muchos con categories (usa la tabla intermedia)
    categorias = db.relationship('Category', secondary=product_categories,
                                backref=db.backref('products', lazy='dynamic'))

    # Relación uno a muchos con variantes
    variantes  = db.relationship('ProductVariant', backref='producto', lazy=True,
                                cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Product {self.nombre}>'

    @property
    def sin_stock(self):
        # Propiedad calculada: True si no hay stock disponible
        return self.stock <= 0

    @property
    def stock_bajo(self):
        # True si el stock está por debajo del mínimo configurado
        return 0 < self.stock <= self.stock_minimo

# ── Variantes de producto ────────────────────────────────────────────────────
class ProductVariant(db.Model):
    __tablename__ = 'product_variants'

    id           = db.Column(db.Integer, primary_key=True)
    producto_id  = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    nombre       = db.Column(db.String(100), nullable=False)  # ej: "Fragancia"
    valor        = db.Column(db.String(100), nullable=False)  # ej: "Lavanda"
    stock        = db.Column(db.Integer, default=0)
    precio_extra = db.Column(db.Numeric(10, 2), default=0)

    def __repr__(self):
        return f'<Variant {self.nombre}: {self.valor}>'

# ── Usuarios ─────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    nombre        = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol           = db.Column(db.String(20), nullable=False)  # 'vendedor' o 'admin'
    activo        = db.Column(db.Boolean, default=True)
    creado_en     = db.Column(db.DateTime, default=datetime.utcnow)

    ventas = db.relationship('Sale', backref='usuario', lazy=True)

    # Métodos para manejar contraseña con hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def es_admin(self):
        return self.rol == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'

# ── Ventas ───────────────────────────────────────────────────────────────────
class Sale(db.Model):
    __tablename__ = 'sales'

    id               = db.Column(db.Integer, primary_key=True)
    usuario_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tipo             = db.Column(db.String(20), nullable=False)  # 'whatsapp' o 'pos'
    estado           = db.Column(db.String(20), default='completada')
    total            = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago      = db.Column(db.String(50))
    nombre_cliente   = db.Column(db.String(150))
    telefono_cliente = db.Column(db.String(30))
    notas            = db.Column(db.Text)
    creado_en        = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('SaleItem', backref='venta', lazy=True,
                            cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Sale #{self.id} ${self.total}>'

# ── Items de venta ────────────────────────────────────────────────────────────
class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id              = db.Column(db.Integer, primary_key=True)
    venta_id        = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    producto_id     = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variante_id     = db.Column(db.Integer, db.ForeignKey('product_variants.id'))
    nombre_producto = db.Column(db.String(200), nullable=False)  # snapshot
    cantidad        = db.Column(db.Integer, nullable=False)
    tipo_precio     = db.Column(db.String(20))   # 'unidad', 'mayor', 'caja'
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # snapshot
    subtotal        = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<SaleItem {self.nombre_producto} x{self.cantidad}>'

# ── Movimientos de stock ──────────────────────────────────────────────────────
class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id          = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variante_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'))
    usuario_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tipo        = db.Column(db.String(20), nullable=False)  # 'entrada', 'salida', 'ajuste'
    cantidad    = db.Column(db.Integer, nullable=False)
    motivo      = db.Column(db.String(200))
    creado_en   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StockMovement {self.tipo} {self.cantidad}>'

# ── Configuración de la tienda ────────────────────────────────────────────────
class StoreConfig(db.Model):
    __tablename__ = 'store_config'

    id          = db.Column(db.Integer, primary_key=True)
    clave       = db.Column(db.String(100), unique=True, nullable=False)
    valor       = db.Column(db.Text)
    descripcion = db.Column(db.String(200))

    def __repr__(self):
        return f'<StoreConfig {self.clave}>'
