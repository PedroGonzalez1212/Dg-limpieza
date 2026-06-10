from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required, current_user
from app.utils.decorators import vendedor_required
from app.models import Product, ProductVariant, Sale, SaleItem, StockMovement
from app import db
from decimal import Decimal

vendedor_bp = Blueprint('panel', __name__)


# ── Dashboard ────────────────────────────────────────────────────────────────

@vendedor_bp.route('/')
@login_required
@vendedor_required
def dashboard():
    from app.models import Sale
    pedidos_pendientes = 0
    if current_user.es_admin():
        pedidos_pendientes = Sale.query.filter_by(
            tipo='whatsapp', estado='pendiente'
        ).count()
    return render_template('panel/dashboard.html',
        pedidos_pendientes=pedidos_pendientes)


# ── POS — Pantalla principal ─────────────────────────────────────────────────

@vendedor_bp.route('/pos')
@login_required
@vendedor_required
def pos():
    """
    Renderiza la pantalla del POS.
    El carrito del POS vive en session['carrito_pos'] — igual que el carrito
    público pero con clave distinta para que no se mezclen.
    """
    carrito = session.get('carrito_pos', {})

    # Calculamos el total sumando los subtotales de cada item
    total = sum(Decimal(str(item['subtotal'])) for item in carrito.values())

    return render_template('panel/pos.html',
                        carrito=carrito,
                        total=total)


# ── POS — Buscar productos (AJAX) ────────────────────────────────────────────

@vendedor_bp.route('/pos/buscar')
@login_required
@vendedor_required
def pos_buscar():
    """
    Endpoint AJAX que devuelve productos en formato JSON.
    El frontend llama esto cada vez que el vendedor tipea en el buscador.

    ?q=lavandina  →  busca productos cuyo nombre contenga "lavandina"
    """
    q = request.args.get('q', '').strip()

    if len(q) < 2:
        # No buscamos con menos de 2 caracteres para no traer toda la DB
        return jsonify([])

    productos = Product.query.filter(
        Product.nombre.ilike(f'%{q}%'),
        Product.activo == True,
        Product.stock > 0          # En el POS solo mostramos productos con stock
    ).limit(10).all()

    # Armamos la lista que el JS va a usar para mostrar los resultados
    resultado = []
    for p in productos:
        item = {
            'id': p.id,
            'nombre': p.nombre,
            'stock': p.stock,
            'precio_unidad': float(p.precio_unidad),
            'precio_mayor': float(p.precio_mayor) if p.precio_mayor else None,
            'precio_caja': float(p.precio_caja) if p.precio_caja else None,
            'cantidad_mayor': p.cantidad_mayor,
            'unidades_por_caja': p.unidades_por_caja,
            'tiene_variantes': p.tiene_variantes,
            'variantes': []
        }
        if p.tiene_variantes:
            item['variantes'] = [
                {'id': v.id, 'nombre': v.nombre, 'valor': v.valor, 'stock': v.stock}
                for v in p.variantes if v.stock > 0
            ]
        resultado.append(item)

    return jsonify(resultado)


# ── POS — Agregar al carrito ──────────────────────────────────────────────────

@vendedor_bp.route('/pos/agregar', methods=['POST'])
@login_required
@vendedor_required
def pos_agregar():
    """
    Recibe un producto del frontend y lo agrega al carrito en sesión.
    Devuelve JSON con el estado actualizado del carrito.

    Por qué usamos la sesión y no la DB:
    El carrito es temporal. Solo lo guardamos en la DB cuando la venta
    se confirma. Así evitamos ventas incompletas en la tabla sales.
    """
    data = request.get_json()

    producto_id = data.get('producto_id')
    variante_id = data.get('variante_id')
    cantidad    = int(data.get('cantidad', 1))

    producto = Product.query.get_or_404(producto_id)

    # Determinamos el precio según la cantidad (misma lógica que el carrito público)
    precio = Decimal(str(producto.precio_unidad))
    tipo_precio = 'unidad'

    if producto.unidades_por_caja and cantidad >= producto.unidades_por_caja and producto.precio_caja:
        precio = Decimal(str(producto.precio_caja))
        tipo_precio = 'caja'
    elif producto.cantidad_mayor and cantidad >= producto.cantidad_mayor and producto.precio_mayor:
        precio = Decimal(str(producto.precio_mayor))
        tipo_precio = 'mayor'

    subtotal = precio * cantidad

    # La clave del carrito es "producto_id" o "producto_id_variante_id"
    # para que el mismo producto con distintas variantes ocupe filas separadas
    clave = str(producto_id)
    if variante_id:
        clave = f"{producto_id}_{variante_id}"
        variante = ProductVariant.query.get(variante_id)
        nombre_completo = f"{producto.nombre} ({variante.valor})"
    else:
        nombre_completo = producto.nombre

    carrito = session.get('carrito_pos', {})

    if clave in carrito:
        # Si ya está en el carrito, sumamos la cantidad
        nueva_cantidad = carrito[clave]['cantidad'] + cantidad
        nuevo_subtotal = precio * nueva_cantidad
        carrito[clave]['cantidad'] = nueva_cantidad
        carrito[clave]['subtotal'] = float(nuevo_subtotal)
        carrito[clave]['tipo_precio'] = tipo_precio
    else:
        carrito[clave] = {
            'producto_id': producto_id,
            'variante_id': variante_id,
            'nombre': nombre_completo,
            'cantidad': cantidad,
            'precio_unitario': float(precio),
            'subtotal': float(subtotal),
            'tipo_precio': tipo_precio
        }

    # IMPORTANTE: reasignamos la sesión para que Flask detecte el cambio
    # Flask solo guarda la sesión si detecta que cambió. Si modificamos
    # un objeto anidado sin reasignar, puede no guardar.
    session['carrito_pos'] = carrito
    session.modified = True

    total = sum(Decimal(str(i['subtotal'])) for i in carrito.values())

    return jsonify({
        'ok': True,
        'carrito': carrito,
        'total': float(total),
        'items_count': len(carrito)
    })


# ── POS — Quitar del carrito ──────────────────────────────────────────────────

@vendedor_bp.route('/pos/quitar', methods=['POST'])
@login_required
@vendedor_required
def pos_quitar():
    """Elimina un item del carrito por su clave."""
    data  = request.get_json()
    clave = data.get('clave')

    carrito = session.get('carrito_pos', {})
    carrito.pop(clave, None)
    session['carrito_pos'] = carrito
    session.modified = True

    total = sum(Decimal(str(i['subtotal'])) for i in carrito.values())

    return jsonify({'ok': True, 'total': float(total), 'items_count': len(carrito)})


# ── POS — Confirmar venta ─────────────────────────────────────────────────────

@vendedor_bp.route('/pos/confirmar', methods=['POST'])
@login_required
@vendedor_required
def pos_confirmar():
    """
    El corazón del POS. Cuando el vendedor confirma la venta:

    1. Crea el registro Sale en la DB
    2. Crea un SaleItem por cada producto
    3. Descuenta el stock del Product (y de la Variante si aplica)
    4. Registra un StockMovement por cada item (auditoría)
    5. Limpia el carrito de la sesión
    6. Devuelve los datos para armar el comprobante de WhatsApp

    Todo esto ocurre en una sola transacción de DB.
    Si algo falla a mitad, SQLAlchemy hace rollback automático
    y la DB queda en el estado anterior — sin ventas fantasma ni stock mal descontado.
    """
    data         = request.get_json()
    metodo_pago  = data.get('metodo_pago')
    nombre_cliente = data.get('nombre_cliente', '').strip()
    telefono_cliente = data.get('telefono_cliente', '').strip()

    carrito = session.get('carrito_pos', {})

    if not carrito:
        return jsonify({'ok': False, 'error': 'El carrito está vacío'}), 400

    if not metodo_pago:
        return jsonify({'ok': False, 'error': 'Seleccioná un método de pago'}), 400

    try:
        total = sum(Decimal(str(i['subtotal'])) for i in carrito.values())

        # 1. Crear la venta
        venta = Sale(
            usuario_id       = current_user.id,
            tipo             = 'pos',
            estado           = 'completada',
            total            = total,
            metodo_pago      = metodo_pago,
            nombre_cliente   = nombre_cliente or None,
            telefono_cliente = telefono_cliente or None
        )
        db.session.add(venta)
        db.session.flush()  # flush asigna el id a venta sin hacer commit todavía
                            # lo necesitamos para asociar los SaleItems

        items_comprobante = []

        for clave, item in carrito.items():
            producto = Product.query.get(item['producto_id'])

            if not producto:
                continue

            # 2. Crear el item de venta (snapshot del precio al momento de la venta)
            sale_item = SaleItem(
                venta_id        = venta.id,
                producto_id     = item['producto_id'],
                variante_id     = item.get('variante_id'),
                nombre_producto = item['nombre'],
                cantidad        = item['cantidad'],
                tipo_precio     = item['tipo_precio'],
                precio_unitario = Decimal(str(item['precio_unitario'])),
                subtotal        = Decimal(str(item['subtotal']))
            )
            db.session.add(sale_item)

            # 3. Descontar stock
            if item.get('variante_id'):
                variante = ProductVariant.query.get(item['variante_id'])
                if variante:
                    variante.stock -= item['cantidad']
            else:
                producto.stock -= item['cantidad']

            # 4. Registrar movimiento de stock (auditoría)
            movimiento = StockMovement(
                producto_id = item['producto_id'],
                variante_id = item.get('variante_id'),
                usuario_id  = current_user.id,
                tipo        = 'salida',
                cantidad    = item['cantidad'],
                motivo      = f"Venta POS #{venta.id}"
            )
            db.session.add(movimiento)

            items_comprobante.append({
                'nombre': item['nombre'],
                'cantidad': item['cantidad'],
                'precio_unitario': item['precio_unitario'],
                'subtotal': item['subtotal'],
                'tipo_precio': item['tipo_precio']
            })

        # 5. Commit: todo se guarda junto o todo se cancela
        db.session.commit()

        # 6. Limpiar el carrito
        session.pop('carrito_pos', None)
        session.modified = True

        # 7. Devolver datos para el comprobante
        return jsonify({
            'ok': True,
            'venta_id': venta.id,
            'total': float(total),
            'metodo_pago': metodo_pago,
            'nombre_cliente': nombre_cliente,
            'telefono_cliente': telefono_cliente,
            'items': items_comprobante
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500