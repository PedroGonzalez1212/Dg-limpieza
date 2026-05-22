from flask import Blueprint, render_template, abort
from app.models import Product, Category

catalogo_bp = Blueprint('catalogo', __name__)


@catalogo_bp.route('/catalogo')
def catalogo():
    """
    Ruta del catálogo — ya estaba hecha en el Sprint 1.
    La dejamos acá para tener todo lo público en un solo archivo.
    """
    from flask import request
    categoria_slug = request.args.get('categoria', '')
    busqueda = request.args.get('q', '').strip()

    query = Product.query.filter_by(activo=True)

    if categoria_slug:
        query = query.join(Product.categorias).filter(Category.slug == categoria_slug)

    if busqueda:
        query = query.filter(Product.nombre.ilike(f'%{busqueda}%'))

    productos = query.order_by(Product.nombre).all()
    categorias = Category.query.filter_by(activa=True).all()

    return render_template('catalogo.html',
                        productos=productos,
                        categorias=categorias,
                        categoria_activa=categoria_slug,
                        busqueda=busqueda)


@catalogo_bp.route('/producto/<int:producto_id>')
def detalle(producto_id):
    """
    Ruta de detalle de producto.

    ¿Por qué <int:producto_id>?
    Flask convierte automáticamente el segmento de la URL a entero.
    Si alguien pone /producto/abc Flask devuelve 404 solo, sin que
    tengamos que validar nada manualmente.

    abort(404): si el producto no existe o está inactivo, Flask muestra
    la página de error 404 estándar. Más adelante podemos personalizar
    esa página.
    """
    producto = Product.query.filter_by(id=producto_id, activo=True).first()

    if not producto:
        abort(404)

    # Agrupamos las variantes por nombre de atributo para mostrarlas
    # ordenadas en el template. Ejemplo:
    # { "Fragancia": ["Lavanda", "Limón"], "Tamaño": ["1L", "5L"] }
    variantes_agrupadas = {}
    for v in producto.variantes:
        if v.nombre not in variantes_agrupadas:
            variantes_agrupadas[v.nombre] = []
        variantes_agrupadas[v.nombre].append(v)

    # Productos relacionados: otros productos de la misma categoría,
    # máximo 4, excluyendo el actual.
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

    return render_template('detalle.html',
                          producto=producto,
                          variantes_agrupadas=variantes_agrupadas,
                          relacionados=relacionados)