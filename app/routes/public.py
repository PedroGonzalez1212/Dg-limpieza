from flask import Blueprint, render_template, request, abort
from app.models import Product, Category

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def home():
    return render_template('public/home.html')

@public_bp.route('/catalogo')
def catalogo():
    # Leemos los filtros que vienen en la URL
    # Ej: /catalogo?categoria=limpieza&q=detergente
    categoria_slug = request.args.get('categoria', '')  # '' = todas
    busqueda = request.args.get('q', '').strip()

    # Construimos la query de forma progresiva.
    # Esto se llama "query building" — arrancamos con todos los productos
    # activos y vamos agregando filtros solo si el usuario los pidió.
    query = Product.query.filter_by(activo=True)

    if categoria_slug:
        # Filtramos por categoría usando la relación muchos-a-muchos.
        # .has() busca si alguna categoría asociada cumple la condición.
        query = query.filter(
            Product.categorias.any(slug=categoria_slug)
        )

    if busqueda:
        # ILIKE es búsqueda case-insensitive (ignora mayúsculas/minúsculas).
        # El % es el wildcard: %detergente% encuentra "Detergente Magistral".
        query = query.filter(
            Product.nombre.ilike(f'%{busqueda}%')
        )

    productos = query.order_by(Product.nombre).all()
    categorias = Category.query.filter_by(activa=True).all()

    return render_template('public/catalogo.html',
        productos=productos,
        categorias=categorias,
        categoria_activa=categoria_slug,
        busqueda=busqueda
    )

@public_bp.route('/producto/<int:producto_id>')
def detalle_producto(producto_id):
    from app.models import Product, Category
    producto = Product.query.filter_by(id=producto_id, activo=True).first()
    if not producto:
        abort(404)

    variantes_agrupadas = {}
    for v in producto.variantes:
        if v.nombre not in variantes_agrupadas:
            variantes_agrupadas[v.nombre] = []
        variantes_agrupadas[v.nombre].append(v)

    relacionados = []
    if producto.categorias:
        primera_categoria = producto.categorias[0]
        relacionados = (Product.query
                        .filter(Product.activo == True)
                        .filter(Product.id != producto.id)
                        .join(Product.categorias)
                        .filter(Category.id == primera_categoria.id)
                        .limit(4)
                        .all())

    return render_template('public/detalle.html',
                        producto=producto,
                        variantes_agrupadas=variantes_agrupadas,
                        relacionados=relacionados)

# ─────────────────────────────────────────────────────────────
# CARRITO — Rutas a agregar en app/routes/public.py
#
# ¿Por qué session y no DB?
# El carrito es temporal. Guardarlo en session (cookie encriptada
# en el navegador del usuario) es más simple y no ensucia la DB
# con carritos abandonados. Solo tocamos la DB cuando el usuario
# confirma el pedido.
#
# Estructura del carrito en session:
# session['carrito'] = {
#   "9":  {"nombre": "Lavandina", "cantidad": 2, "precio": 150.0, "subtotal": 300.0},
#   "12": {"nombre": "Detergente", "cantidad": 1, "precio": 200.0, "subtotal": 200.0}
# }
# Las claves son strings porque JSON (y las cookies) solo soporta
# claves de diccionario como strings.
# ─────────────────────────────────────────────────────────────

from flask import session, jsonify, request, render_template, redirect, url_for
from app.models import Product


# ── HELPER ────────────────────────────────────────────────────
def _get_precio(producto, variante=None):
    """
    Devuelve el precio unitario del producto.
    
    Por ahora usamos precio_unidad siempre.
    El descuento por cantidad (mayor/caja) se calcula en el frontend
    del detalle, pero al carrito le mandamos precio base. El resumen
    del carrito puede recalcular si querés en el futuro.
    """
    return float(producto.precio_unidad or 0)


# ── AGREGAR AL CARRITO ─────────────────────────────────────────
@public_bp.route('/carrito/agregar', methods=['POST'])
def carrito_agregar():
    """
    Recibe un POST con JSON: { producto_id, variante_id, cantidad }
    Agrega el producto al carrito en session.
    
    ¿Por qué POST y no GET?
    Porque estamos modificando estado (el carrito). GET es para
    leer datos, POST para modificarlos. Es una convención REST.
    
    ¿Por qué devolvemos JSON?
    Porque el frontend llama a esta ruta con fetch() de forma
    asíncrona — no queremos recargar la página, solo actualizar
    el contador del carrito en el navbar.
    """
    data = request.get_json()
    
    producto_id = data.get('producto_id')
    variante_id = data.get('variante_id')
    cantidad = int(data.get('cantidad', 1))

    # Validar que el producto existe y está activo
    producto = Product.query.filter_by(id=producto_id, activo=True).first()
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404

    # Validar stock
    if producto.stock is not None and producto.stock <= 0:
        return jsonify({'error': 'Producto sin stock'}), 400

    # Inicializar el carrito si no existe todavía en la sesión
    if 'carrito' not in session:
        session['carrito'] = {}

    # Usamos el producto_id como clave (string obligatorio en JSON)
    key = str(producto_id)

    precio = _get_precio(producto)

    if key in session['carrito']:
        # Si ya está, sumamos cantidad
        session['carrito'][key]['cantidad'] += cantidad
        session['carrito'][key]['subtotal'] = (
            session['carrito'][key]['cantidad'] * precio
        )
    else:
        # Si es nuevo, lo agregamos
        session['carrito'][key] = {
            'nombre': producto.nombre,
            'precio': precio,
            'cantidad': cantidad,
            'subtotal': precio * cantidad,
            'imagen': producto.imagen_url or '',
            'variante_id': variante_id,
        }

    # IMPORTANTE: Flask no detecta cambios dentro de dicts anidados
    # automáticamente. Hay que marcar la session como modificada
    # para que guarde los cambios en la cookie.
    session.modified = True

    total_items = sum(item['cantidad'] for item in session['carrito'].values())

    return jsonify({
        'ok': True,
        'mensaje': f'"{producto.nombre}" agregado al carrito',
        'total_items': total_items
    })


# ── VER CARRITO ────────────────────────────────────────────────
@public_bp.route('/carrito')
def carrito():
    """
    Muestra la página del carrito con todos los productos.
    """
    carrito = session.get('carrito', {})
    
    total = sum(item['subtotal'] for item in carrito.values())
    total_items = sum(item['cantidad'] for item in carrito.values())

    return render_template('public/carrito.html',
                           carrito=carrito,
                           total=total,
                           total_items=total_items)


# ── ACTUALIZAR CANTIDAD ────────────────────────────────────────
@public_bp.route('/carrito/actualizar', methods=['POST'])
def carrito_actualizar():
    """
    Cambia la cantidad de un producto en el carrito.
    Si cantidad llega a 0, elimina el producto.
    """
    data = request.get_json()
    key = str(data.get('producto_id'))
    nueva_cantidad = int(data.get('cantidad', 1))

    carrito = session.get('carrito', {})

    if key not in carrito:
        return jsonify({'error': 'Producto no está en el carrito'}), 404

    if nueva_cantidad <= 0:
        del carrito[key]
    else:
        carrito[key]['cantidad'] = nueva_cantidad
        carrito[key]['subtotal'] = nueva_cantidad * carrito[key]['precio']

    session['carrito'] = carrito
    session.modified = True

    total = sum(item['subtotal'] for item in carrito.values())
    total_items = sum(item['cantidad'] for item in carrito.values())

    return jsonify({
        'ok': True,
        'total': total,
        'total_items': total_items,
        'subtotal': carrito.get(key, {}).get('subtotal', 0)
    })


# ── ELIMINAR PRODUCTO ──────────────────────────────────────────
@public_bp.route('/carrito/eliminar', methods=['POST'])
def carrito_eliminar():
    """
    Elimina un producto del carrito por su producto_id.
    """
    data = request.get_json()
    key = str(data.get('producto_id'))

    carrito = session.get('carrito', {})
    carrito.pop(key, None)  # pop con default None no rompe si no existe
    session['carrito'] = carrito
    session.modified = True

    total = sum(item['subtotal'] for item in carrito.values())
    total_items = sum(item['cantidad'] for item in carrito.values())

    return jsonify({'ok': True, 'total': total, 'total_items': total_items})


# ── VACIAR CARRITO ─────────────────────────────────────────────
@public_bp.route('/carrito/vaciar', methods=['POST'])
def carrito_vaciar():
    """
    Limpia el carrito completo. Se usa después de confirmar el pedido.
    """
    session.pop('carrito', None)
    session.modified = True
    return jsonify({'ok': True})

@public_bp.route('/carrito/total')
def carrito_total():
    """
    Devuelve la cantidad de items en el carrito.
    La usa el navbar en todas las páginas para mostrar el badge.
    Es una ruta GET simple — no modifica nada.
    """
    carrito = session.get('carrito', {})
    total = sum(item['cantidad'] for item in carrito.values())
    return jsonify({'total_items': total})

@public_bp.route('/contacto')
def contacto():
    return render_template('public/home.html')  # temporal