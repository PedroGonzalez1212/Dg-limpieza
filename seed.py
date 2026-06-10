"""
seed.py — Datos de prueba para DG Limpieza
Ejecutar desde la raíz del proyecto:
    python seed.py

IMPORTANTE: Borra todos los datos existentes antes de insertar.
No correr en producción.
"""

from app import create_app, db
from app.models import (
    Category, Product, ProductVariant,
    User, StoreConfig
)

app = create_app()

def seed():
    with app.app_context():

        # ── Limpieza previa ──────────────────────────────────────────────────
        # Borramos en orden inverso a las dependencias para no violar
        # las foreign keys (variantes antes que productos, etc.)
        print("🗑️  Limpiando tablas...")
        ProductVariant.query.delete()
        Product.query.delete()
        Category.query.delete()
        User.query.delete()
        StoreConfig.query.delete()
        db.session.commit()

        # ── Categorías ───────────────────────────────────────────────────────
        # El slug es la versión URL-friendly del nombre.
        # Lo usamos para filtrar: /catalogo?categoria=limpieza
        print("📂 Creando categorías...")
        cats = {
            'limpieza':     Category(nombre='Limpieza',      slug='limpieza',     icono='spray-can'),
            'descartables': Category(nombre='Descartables',  slug='descartables', icono='cup-straw'),
            'perfumeria':   Category(nombre='Perfumería',    slug='perfumeria',   icono='bottle'),
            'piscinas':     Category(nombre='Piscinas',      slug='piscinas',     icono='pool'),
            'bolsas':       Category(nombre='Bolsas',        slug='bolsas',       icono='bag'),
        }
        for cat in cats.values():
            db.session.add(cat)
        db.session.commit()

        # ── Helper para imágenes ─────────────────────────────────────────────
        # Usamos placeholder.com para tener imágenes reales mientras no hay fotos.
        # El color de fondo varía por categoría para distinguirlas visualmente.
        def img(color, texto):
            texto_encoded = texto.replace(' ', '+')
            return f'https://placehold.co/400x400/{color}/ffffff?text={texto_encoded}'

        # ── Productos ────────────────────────────────────────────────────────
        # Nomenclatura de precios real de distribuidora:
        # precio_unidad  → 1 unidad suelta
        # precio_mayor   → precio al por mayor (requiere cantidad_mayor mínima)
        # precio_caja    → precio por caja cerrada (unidades_por_caja unidades)
        print("📦 Creando productos...")

        productos = [

            # ══ LIMPIEZA ══════════════════════════════════════════════════════

            Product(
                nombre='Detergente Magistral 500ml',
                descripcion='Detergente líquido concentrado para vajilla. Alta espuma, aroma limón.',
                imagen_url=img('1a73e8', 'Detergente'),
                precio_unidad=1200,
                precio_mayor=1050,
                precio_caja=950,
                cantidad_mayor=12,
                unidades_por_caja=24,
                stock=80,
                stock_minimo=10,
                tiene_variantes=True,
                categorias=[cats['limpieza']]
            ),

            Product(
                nombre='Lavandina Concentrada 1L',
                descripcion='Lavandina al 55g/L. Desinfecta, blanquea y elimina bacterias y hongos.',
                imagen_url=img('1a73e8', 'Lavandina'),
                precio_unidad=900,
                precio_mayor=780,
                precio_caja=720,
                cantidad_mayor=12,
                unidades_por_caja=12,
                stock=120,
                stock_minimo=15,
                tiene_variantes=False,
                categorias=[cats['limpieza']]
            ),

            Product(
                nombre='Limpiador Multiuso Poett 500ml',
                descripcion='Limpiador perfumado para todas las superficies del hogar.',
                imagen_url=img('1a73e8', 'Poett'),
                precio_unidad=1500,
                precio_mayor=1300,
                precio_caja=1200,
                cantidad_mayor=6,
                unidades_por_caja=12,
                stock=60,
                stock_minimo=8,
                tiene_variantes=True,
                categorias=[cats['limpieza']]
            ),

            Product(
                nombre='Desengrasante Industrial 1L',
                descripcion='Desengrasante concentrado para cocinas industriales y domésticas.',
                imagen_url=img('1a73e8', 'Desengrasante'),
                precio_unidad=1800,
                precio_mayor=1580,
                precio_caja=1450,
                cantidad_mayor=6,
                unidades_por_caja=12,
                stock=3,  # Stock bajo → dispara alerta
                stock_minimo=5,
                tiene_variantes=False,
                categorias=[cats['limpieza']]
            ),

            Product(
                nombre='Jabón en Polvo Ariel 1kg',
                descripcion='Detergente en polvo para ropa blanca y de color. Acción profunda.',
                imagen_url=img('1a73e8', 'Ariel'),
                precio_unidad=2200,
                precio_mayor=1950,
                precio_caja=1800,
                cantidad_mayor=6,
                unidades_por_caja=10,
                stock=0,  # Sin stock → bloqueado en carrito
                stock_minimo=5,
                tiene_variantes=False,
                categorias=[cats['limpieza']]
            ),

            Product(
                nombre='Esponja Multiuso x3',
                descripcion='Pack de 3 esponjas doble cara para vajilla y superficies.',
                imagen_url=img('1a73e8', 'Esponjas'),
                precio_unidad=600,
                precio_mayor=520,
                precio_caja=480,
                cantidad_mayor=10,
                unidades_por_caja=24,
                stock=200,
                stock_minimo=20,
                tiene_variantes=False,
                categorias=[cats['limpieza']]
            ),

            # ══ DESCARTABLES ═════════════════════════════════════════════════

            Product(
                nombre='Vasos Descartables 250ml x50',
                descripcion='Vasos plásticos transparentes. Pack de 50 unidades.',
                imagen_url=img('2e7d32', 'Vasos'),
                precio_unidad=800,
                precio_mayor=700,
                precio_caja=650,
                cantidad_mayor=10,
                unidades_por_caja=20,
                stock=150,
                stock_minimo=15,
                tiene_variantes=False,
                categorias=[cats['descartables']]
            ),

            Product(
                nombre='Platos Descartables 23cm x25',
                descripcion='Platos de telgopor resistentes. Pack de 25 unidades.',
                imagen_url=img('2e7d32', 'Platos'),
                precio_unidad=950,
                precio_mayor=830,
                precio_caja=760,
                cantidad_mayor=10,
                unidades_por_caja=20,
                stock=90,
                stock_minimo=10,
                tiene_variantes=False,
                categorias=[cats['descartables']]
            ),

            Product(
                nombre='Cubiertos Descartables x50',
                descripcion='Set tenedor, cuchillo y cuchara. Plástico resistente.',
                imagen_url=img('2e7d32', 'Cubiertos'),
                precio_unidad=1100,
                precio_mayor=960,
                precio_caja=880,
                cantidad_mayor=10,
                unidades_por_caja=20,
                stock=70,
                stock_minimo=10,
                tiene_variantes=False,
                categorias=[cats['descartables']]
            ),

            Product(
                nombre='Bandeja Aluminio N°3',
                descripcion='Bandeja de aluminio para horno. Resistente a altas temperaturas.',
                imagen_url=img('2e7d32', 'Bandeja'),
                precio_unidad=350,
                precio_mayor=300,
                precio_caja=270,
                cantidad_mayor=24,
                unidades_por_caja=50,
                stock=400,
                stock_minimo=30,
                tiene_variantes=False,
                categorias=[cats['descartables']]
            ),

            # ══ PERFUMERÍA ════════════════════════════════════════════════════

            Product(
                nombre='Suavizante de Ropa Comfort 1L',
                descripcion='Suavizante concentrado para todo tipo de telas.',
                imagen_url=img('7b1fa2', 'Suavizante'),
                precio_unidad=1600,
                precio_mayor=1400,
                precio_caja=1280,
                cantidad_mayor=6,
                unidades_por_caja=12,
                stock=55,
                stock_minimo=8,
                tiene_variantes=True,
                categorias=[cats['perfumeria']]
            ),

            Product(
                nombre='Desodorante de Ambiente 360ml',
                descripcion='Aerosol de larga duración. Elimina olores y perfuma el ambiente.',
                imagen_url=img('7b1fa2', 'Desodorante'),
                precio_unidad=1900,
                precio_mayor=1680,
                precio_caja=1550,
                cantidad_mayor=6,
                unidades_por_caja=12,
                stock=40,
                stock_minimo=6,
                tiene_variantes=True,
                categorias=[cats['perfumeria']]
            ),

            Product(
                nombre='Jabón Líquido Manos 500ml',
                descripcion='Jabón antibacterial con hidratantes. Aroma frutal.',
                imagen_url=img('7b1fa2', 'Jabon'),
                precio_unidad=1100,
                precio_mayor=960,
                precio_caja=880,
                cantidad_mayor=6,
                unidades_por_caja=12,
                stock=85,
                stock_minimo=10,
                tiene_variantes=False,
                categorias=[cats['perfumeria']]
            ),

            # ══ PISCINAS ══════════════════════════════════════════════════════

            Product(
                nombre='Cloro Granulado 1kg',
                descripcion='Hipoclorito de calcio al 65%. Para desinfección de piscinas.',
                imagen_url=img('00838a', 'Cloro'),
                precio_unidad=3500,
                precio_mayor=3100,
                precio_caja=2900,
                cantidad_mayor=6,
                unidades_por_caja=12,
                stock=35,
                stock_minimo=6,
                tiene_variantes=False,
                categorias=[cats['piscinas']]
            ),

            Product(
                nombre='Algicida Mantenimiento 1L',
                descripcion='Previene y elimina algas en piscinas. Producto concentrado.',
                imagen_url=img('00838a', 'Algicida'),
                precio_unidad=2800,
                precio_mayor=2450,
                precio_caja=2250,
                cantidad_mayor=6,
                unidades_por_caja=6,
                stock=20,
                stock_minimo=4,
                tiene_variantes=False,
                categorias=[cats['piscinas']]
            ),

            Product(
                nombre='Clarificante Floculante 1L',
                descripcion='Aclara el agua turbia de la piscina. Acción rápida.',
                imagen_url=img('00838a', 'Floculante'),
                precio_unidad=2400,
                precio_mayor=2100,
                precio_caja=1950,
                cantidad_mayor=6,
                unidades_por_caja=6,
                stock=0,  # Sin stock
                stock_minimo=3,
                tiene_variantes=False,
                categorias=[cats['piscinas']]
            ),

            # ══ BOLSAS ════════════════════════════════════════════════════════

            Product(
                nombre='Bolsas de Residuos Negras 60L x10',
                descripcion='Bolsas resistentes para residuos domésticos. Pack de 10.',
                imagen_url=img('424242', 'Bolsas+60L'),
                precio_unidad=700,
                precio_mayor=610,
                precio_caja=560,
                cantidad_mayor=12,
                unidades_por_caja=24,
                stock=300,
                stock_minimo=20,
                tiene_variantes=False,
                categorias=[cats['bolsas']]
            ),

            Product(
                nombre='Bolsas de Residuos Negras 100L x10',
                descripcion='Bolsas extra grandes para residuos voluminosos. Pack de 10.',
                imagen_url=img('424242', 'Bolsas+100L'),
                precio_unidad=950,
                precio_mayor=830,
                precio_caja=760,
                cantidad_mayor=12,
                unidades_por_caja=20,
                stock=180,
                stock_minimo=15,
                tiene_variantes=False,
                categorias=[cats['bolsas']]
            ),

            Product(
                nombre='Bolsas Transparentes x100',
                descripcion='Bolsas polietileno transparente para alimentos y uso general.',
                imagen_url=img('424242', 'Bolsas+Transp'),
                precio_unidad=1200,
                precio_mayor=1050,
                precio_caja=960,
                cantidad_mayor=10,
                unidades_por_caja=20,
                stock=250,
                stock_minimo=20,
                tiene_variantes=False,
                categorias=[cats['bolsas']]
            ),

            Product(
                nombre='Bolsas con Cierre Zip x25',
                descripcion='Bolsas reutilizables con cierre hermético. Ideales para alimentos.',
                imagen_url=img('424242', 'Bolsas+Zip'),
                precio_unidad=850,
                precio_mayor=740,
                precio_caja=680,
                cantidad_mayor=10,
                unidades_por_caja=20,
                stock=4,  # Stock bajo
                stock_minimo=5,
                tiene_variantes=False,
                categorias=[cats['bolsas']]
            ),
        ]

        for p in productos:
            db.session.add(p)
        db.session.commit()

        # ── Variantes ────────────────────────────────────────────────────────
        # Solo los productos con tiene_variantes=True.
        # Las búscamos por nombre para no depender de IDs hardcodeados.
        print("🎨 Creando variantes...")

        # Detergente Magistral → variantes de fragancia
        detergente = Product.query.filter_by(nombre='Detergente Magistral 500ml').first()
        for fragancia in ['Limón', 'Naranja', 'Manzana']:
            db.session.add(ProductVariant(
                producto_id=detergente.id,
                nombre='Fragancia',
                valor=fragancia,
                stock=25,
                precio_extra=0
            ))

        # Poett → variantes de fragancia
        poett = Product.query.filter_by(nombre='Limpiador Multiuso Poett 500ml').first()
        for fragancia in ['Lavanda', 'Bebé', 'Floral', 'Frutal']:
            db.session.add(ProductVariant(
                producto_id=poett.id,
                nombre='Fragancia',
                valor=fragancia,
                stock=15,
                precio_extra=0
            ))

        # Suavizante Comfort → variantes de fragancia + precio extra en algunas
        suavizante = Product.query.filter_by(nombre='Suavizante de Ropa Comfort 1L').first()
        variantes_suavizante = [
            ('Primavera', 0),
            ('Bebé', 50),       # Premium → $50 extra
            ('Sport', 0),
            ('Clásico', 0),
        ]
        for fragancia, extra in variantes_suavizante:
            db.session.add(ProductVariant(
                producto_id=suavizante.id,
                nombre='Fragancia',
                valor=fragancia,
                stock=12,
                precio_extra=extra
            ))

        # Desodorante de Ambiente → variantes de fragancia
        desodorante = Product.query.filter_by(nombre='Desodorante de Ambiente 360ml').first()
        for fragancia in ['Lavanda', 'Citrus', 'Vainilla', 'Floral']:
            db.session.add(ProductVariant(
                producto_id=desodorante.id,
                nombre='Fragancia',
                valor=fragancia,
                stock=10,
                precio_extra=0
            ))

        db.session.commit()

        # ── Usuarios ─────────────────────────────────────────────────────────
        print("👤 Creando usuarios...")

        admin = User(
            nombre='Admin DG',
            email='admin@dglimpieza.com',
            rol='admin',
            activo=True
        )
        admin.set_password('admin1234')

        vendedor = User(
            nombre='Vendedor 1',
            email='vendedor@dglimpieza.com',
            rol='vendedor',
            activo=True
        )
        vendedor.set_password('vendedor1234')

        db.session.add_all([admin, vendedor])
        db.session.commit()

        # ── Configuración de la tienda ────────────────────────────────────────
        # Pares clave-valor que el panel admin va a poder editar después.
        print("⚙️  Creando configuración inicial de la tienda...")

        configs = [
            StoreConfig(clave='nombre_tienda',   valor='DG Limpieza',              descripcion='Nombre visible en la tienda'),
            StoreConfig(clave='whatsapp_numero',  valor='5493512515999',            descripcion='Número de WhatsApp sin + ni espacios'),
            StoreConfig(clave='whatsapp_mensaje', valor='Hola! Quiero hacer un pedido:', descripcion='Mensaje inicial del checkout'),
            StoreConfig(clave='moneda',           valor='$',                        descripcion='Símbolo de moneda'),
            StoreConfig(clave='envios_activos',   valor='true',                     descripcion='Si se aceptan envíos a domicilio'),
            StoreConfig(clave='retiro_activo',    valor='true',                     descripcion='Si se acepta retiro en el local'),
        ]
        for c in configs:
            db.session.add(c)
        db.session.commit()

        # ── Resumen final ─────────────────────────────────────────────────────
        print("\n✅ Seed completado exitosamente!")
        print(f"   📂 Categorías: {Category.query.count()}")
        print(f"   📦 Productos:  {Product.query.count()}")
        print(f"   🎨 Variantes:  {ProductVariant.query.count()}")
        print(f"   👤 Usuarios:   {User.query.count()}")
        print(f"   ⚙️  Configs:    {StoreConfig.query.count()}")
        print("\n   Credenciales de prueba:")
        print("   Admin:    admin@dglimpieza.com   / admin1234")
        print("   Vendedor: vendedor@dglimpieza.com / vendedor1234")


if __name__ == '__main__':
    seed()