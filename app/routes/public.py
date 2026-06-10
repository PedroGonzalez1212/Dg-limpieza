from flask import Blueprint, render_template, request, abort, Response
from sqlalchemy import case
from app.models import Product, Category, Combo

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def home():
    combos = Combo.query.filter_by(activo=True).order_by(Combo.creado_en.desc()).all()
    return render_template('public/home.html', combos=combos)

@public_bp.route('/catalogo')
def catalogo():
    # Leemos los filtros que vienen en la URL
    # Ej: /catalogo?categoria=limpieza&q=detergente
    categoria_slug = request.args.get('categoria', '')  # '' = todas
    busqueda = request.args.get('q', '').strip()
    combos = Combo.query.filter_by(activo=True).all()

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

    productos = query.order_by(
        case((Product.stock <= 0, 1), else_=0),
        Product.nombre
    ).all()
    categorias = Category.query.filter_by(activa=True).all()

    return render_template('public/catalogo.html',
        productos=productos,
        categorias=categorias,
        categoria_activa=categoria_slug,
        busqueda=busqueda,
        combos=combos
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


@public_bp.route('/carrito/agregar', methods=['POST'])
def carrito_agregar():
    data = request.get_json()
    
    producto_id = data.get('producto_id')
    variante_id = data.get('variante_id')
    cantidad    = int(data.get('cantidad', 1))
    es_combo    = data.get('es_combo', False)

    if 'carrito' not in session:
        session['carrito'] = {}

    # ── Combo ──────────────────────────────────────────────────
    # Los combos usan la clave "combo_<id>" para no chocar con productos
    if es_combo or (isinstance(producto_id, str) and producto_id.startswith('combo_')):
        combo_id = str(producto_id).replace('combo_', '')
        combo = Combo.query.filter_by(id=combo_id, activo=True).first()
        if not combo:
            return jsonify({'error': 'Combo no encontrado'}), 404

        key   = f'combo_{combo.id}'
        precio = float(combo.precio_combo)

        if key in session['carrito']:
            session['carrito'][key]['cantidad'] += cantidad
            session['carrito'][key]['subtotal']  = session['carrito'][key]['cantidad'] * precio
        else:
            session['carrito'][key] = {
                'nombre':    combo.nombre,
                'precio':    precio,
                'cantidad':  cantidad,
                'subtotal':  precio * cantidad,
                'imagen':    combo.imagen_url or '',
                'variante_id': None,
                'es_combo':  True,
            }

        session.modified = True
        total_items = sum(item['cantidad'] for item in session['carrito'].values())
        return jsonify({
            'ok': True,
            'mensaje': f'"{combo.nombre}" agregado al carrito',
            'total_items': total_items
        })

    # ── Producto normal ────────────────────────────────────────
    producto = Product.query.filter_by(id=producto_id, activo=True).first()
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404

    if producto.stock is not None and producto.stock <= 0:
        return jsonify({'error': 'Producto sin stock'}), 400

    key   = str(producto_id)
    precio = _get_precio(producto)

    if key in session['carrito']:
        session['carrito'][key]['cantidad'] += cantidad
        session['carrito'][key]['subtotal']  = session['carrito'][key]['cantidad'] * precio
    else:
        session['carrito'][key] = {
            'nombre':    producto.nombre,
            'precio':    precio,
            'cantidad':  cantidad,
            'subtotal':  precio * cantidad,
            'imagen':    producto.imagen_url or '',
            'variante_id': variante_id,
            'es_combo':  False,
        }

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

# ── CONFIRMAR PEDIDO (guarda en DB como pendiente) ─────────────
@public_bp.route('/carrito/confirmar', methods=['POST'])
def carrito_confirmar():
    """
    Recibe los datos del cliente y el carrito, guarda el pedido
    en la DB con estado 'pendiente' y devuelve el sale_id.
    
    ¿Por qué guardamos aquí y no cuando el cliente manda el WA?
    Porque no podemos saber si el cliente realmente envió el mensaje
    de WhatsApp — eso pasa fuera de nuestra app. Lo que sí controlamos
    es este momento: el cliente completó el formulario y tocó "Enviar".
    Ese es el momento de registro.
    """
    from app.models import Sale, SaleItem, Product, Combo
    from app import db

    data = request.get_json()
    nombre   = data.get('nombre', '').strip()
    telefono = data.get('telefono', '').strip()
    horario  = data.get('horario', '').strip()

    if not nombre or not telefono or not horario:
        return jsonify({'error': 'Datos incompletos'}), 400

    carrito = session.get('carrito', {})
    if not carrito:
        return jsonify({'error': 'Carrito vacío'}), 400

    # Calculamos el total desde la sesión (fuente de verdad del servidor,
    # no confiamos en el total que muestra el HTML)
    total = sum(item['subtotal'] for item in carrito.values())

    # Usamos usuario_id=1 (admin) como responsable del pedido web.
    # Los pedidos WhatsApp no tienen vendedor asignado — se asigna
    # cuando el vendedor lo confirma desde el panel.
    sale = Sale(
        usuario_id       = 1,
        tipo             = 'whatsapp',
        estado           = 'pendiente',
        total            = total,
        metodo_pago      = None,
        nombre_cliente   = nombre,
        telefono_cliente = telefono,
        notas            = f'Horario de retiro: {horario}',
    )
    db.session.add(sale)
    db.session.flush()  # genera el sale.id sin hacer commit todavía

    # Guardamos cada item del carrito como SaleItem
    for key, item in carrito.items():
        if item.get('es_combo'):
            combo_id    = int(str(key).replace('combo_', ''))
            producto_id = None
        else:
            combo_id    = None
            producto_id = int(key)

        sale_item = SaleItem(
            venta_id        = sale.id,
            producto_id     = producto_id,
            combo_id        = combo_id,
            nombre_producto = item['nombre'],
            cantidad        = item['cantidad'],
            tipo_precio     = 'unidad',
            precio_unitario = item['precio'],
            subtotal        = item['subtotal'],
        )
        db.session.add(sale_item)

    db.session.commit()

    return jsonify({'ok': True, 'sale_id': sale.id})


@public_bp.route('/sitemap.xml')
def sitemap():
    """Genera sitemap dinámico con todas las URLs indexables."""
    from datetime import datetime

    base_url = 'https://dglimpieza.com.ar'
    today = datetime.utcnow().strftime('%Y-%m-%d')

    urls = []

    # Páginas estáticas
    static_pages = [
        ('/', '1.0', 'weekly'),
        ('/catalogo', '0.9', 'daily'),
    ]
    for path, priority, changefreq in static_pages:
        urls.append({
            'loc': base_url + path,
            'lastmod': today,
            'changefreq': changefreq,
            'priority': priority
        })

    # Páginas de categoría
    categorias = Category.query.filter_by(activa=True).all()
    for cat in categorias:
        urls.append({
            'loc': f'{base_url}/catalogo?categoria={cat.slug}',
            'lastmod': today,
            'changefreq': 'weekly',
            'priority': '0.8'
        })

    # Páginas de producto
    productos = Product.query.filter_by(activo=True).all()
    for producto in productos:
        urls.append({
            'loc': f'{base_url}/producto/{producto.id}',
            'lastmod': today,
            'changefreq': 'monthly',
            'priority': '0.6'
        })

    # Generar XML
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in urls:
        xml_lines.append('  <url>')
        xml_lines.append(f'    <loc>{url["loc"]}</loc>')
        xml_lines.append(f'    <lastmod>{url["lastmod"]}</lastmod>')
        xml_lines.append(f'    <changefreq>{url["changefreq"]}</changefreq>')
        xml_lines.append(f'    <priority>{url["priority"]}</priority>')
        xml_lines.append('  </url>')
    xml_lines.append('</urlset>')

    xml_content = '\n'.join(xml_lines)
    return Response(xml_content, mimetype='application/xml')


@public_bp.route('/robots.txt')
def robots():
    """Archivo robots.txt: permite todo excepto rutas internas."""
    content = """User-agent: *
Allow: /
Allow: /catalogo
Allow: /producto/
Disallow: /admin/
Disallow: /panel/
Disallow: /auth/
Disallow: /carrito/

Sitemap: https://dglimpieza.com.ar/sitemap.xml
"""
    return Response(content, mimetype='text/plain')