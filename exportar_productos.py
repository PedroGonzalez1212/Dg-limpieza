import json
from app import create_app
from app.models import Category, Product, ProductVariant

app = create_app()

with app.app_context():
    categorias = [
        {
            "id": c.id,
            "nombre": c.nombre,
            "slug": c.slug,
            "icono": c.icono,
        }
        for c in Category.query.all()
    ]

    productos = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "imagen_url": p.imagen_url,
            "precio_unidad": float(p.precio_unidad) if p.precio_unidad is not None else 0,
            "precio_mayor": float(p.precio_mayor) if p.precio_mayor is not None else 0,
            "precio_caja": float(p.precio_caja) if p.precio_caja is not None else 0,
            "cantidad_mayor": p.cantidad_mayor or 0,
            "unidades_por_caja": p.unidades_por_caja or 0,
            "stock": p.stock,
            "stock_minimo": p.stock_minimo,
            "activo": p.activo,
            "tiene_variantes": p.tiene_variantes,
            "categorias_ids": [c.id for c in p.categorias],
        }
        for p in Product.query.all()
    ]

    variantes = [
        {
            "id": v.id,
            "producto_id": v.producto_id,
            "nombre": v.nombre,
            "valor": v.valor,
            "stock": v.stock,
            "precio_extra": float(v.precio_extra) if v.precio_extra is not None else 0,
        }
        for v in ProductVariant.query.all()
    ]

    data = {
        "categorias": categorias,
        "productos": productos,
        "variantes": variantes,
    }

    with open("productos_export.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Exportados: {len(categorias)} categorías, {len(productos)} productos, {len(variantes)} variantes")
    print("Archivo guardado: productos_export.json")
