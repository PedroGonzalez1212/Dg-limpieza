import json
from app import create_app
from app.models import Category, Product, ProductVariant, db

app = create_app()

with app.app_context():
    with open("productos_export.json", encoding="utf-8") as f:
        data = json.load(f)

    cats_insertadas = 0
    cats_saltadas = 0
    # maps JSON id → DB id
    cat_id_map = {}

    for c in data["categorias"]:
        existente = Category.query.filter_by(slug=c["slug"]).first()
        if existente:
            cat_id_map[c["id"]] = existente.id
            cats_saltadas += 1
        else:
            nueva = Category(
                nombre=c["nombre"],
                slug=c["slug"],
                icono=c.get("icono"),
            )
            db.session.add(nueva)
            db.session.flush()
            cat_id_map[c["id"]] = nueva.id
            cats_insertadas += 1

    prods_insertados = 0
    prods_saltados = 0
    prod_id_map = {}

    for p in data["productos"]:
        existente = Product.query.filter_by(nombre=p["nombre"]).first()
        if existente:
            prod_id_map[p["id"]] = existente.id
            prods_saltados += 1
            continue

        nuevo = Product(
            nombre=p["nombre"],
            descripcion=p.get("descripcion"),
            imagen_url=p.get("imagen_url"),
            precio_unidad=p["precio_unidad"],
            precio_mayor=p.get("precio_mayor"),
            precio_caja=p.get("precio_caja"),
            cantidad_mayor=p.get("cantidad_mayor"),
            unidades_por_caja=p.get("unidades_por_caja"),
            stock=p.get("stock", 0),
            stock_minimo=p.get("stock_minimo", 5),
            activo=p.get("activo", True),
            tiene_variantes=p.get("tiene_variantes", False),
        )

        for json_cat_id in p.get("categorias_ids", []):
            db_cat_id = cat_id_map.get(json_cat_id)
            if db_cat_id:
                cat = Category.query.get(db_cat_id)
                if cat:
                    nuevo.categorias.append(cat)

        db.session.add(nuevo)
        db.session.flush()
        prod_id_map[p["id"]] = nuevo.id
        prods_insertados += 1

    vars_insertadas = 0
    vars_saltadas = 0

    for v in data["variantes"]:
        db_prod_id = prod_id_map.get(v["producto_id"])
        if db_prod_id is None:
            vars_saltadas += 1
            continue

        existente = ProductVariant.query.filter_by(
            producto_id=db_prod_id,
            nombre=v["nombre"],
            valor=v["valor"],
        ).first()
        if existente:
            vars_saltadas += 1
            continue

        nueva = ProductVariant(
            producto_id=db_prod_id,
            nombre=v["nombre"],
            valor=v["valor"],
            stock=v.get("stock", 0),
            precio_extra=v.get("precio_extra", 0),
        )
        db.session.add(nueva)
        vars_insertadas += 1

    db.session.commit()

    print("=== Importación completada ===")
    print(f"Categorías: {cats_insertadas} insertadas, {cats_saltadas} saltadas")
    print(f"Productos:  {prods_insertados} insertados, {prods_saltados} saltados")
    print(f"Variantes:  {vars_insertadas} insertadas, {vars_saltadas} saltadas")
