"""
cleanup_prod.py — Borra datos de prueba de PRODUCCIÓN (Railway/Postgres)

Borra: SaleItem, StockMovement, Sale, ComboItem, Combo (TODOS los registros).
NO toca: Product, Category, User, StoreConfig, product_categories.

Orden de borrado (respeta las foreign keys reales de app/models.py):
    1. SaleItem        (FK -> sales, products, combos, product_variants)
    2. StockMovement   (FK -> products, product_variants, users)
    3. Sale            (ya sin hijos)
    4. ComboItem       (FK -> combos, products)
    5. Combo           (ya sin hijos)

Nota: Sale.items y Combo.items tienen cascade='all, delete-orphan', pero ese
cascade es a nivel de objeto SQLAlchemy y no se dispara con un bulk
Model.query.delete(). Por eso el orden de abajo es explícito.

Ejecutar contra producción con:
    railway run python cleanup_prod.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from app.models import Sale, SaleItem, StockMovement, Combo, ComboItem

app = create_app('production')


def cleanup():
    with app.app_context():
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        # Solo mostramos el host, nunca la URL completa (tiene credenciales)
        host = db_url.split('@')[-1] if '@' in db_url else db_url
        print(f"🔗 Conectado a: {host}\n")

        conteos_antes = {
            'SaleItem':       SaleItem.query.count(),
            'StockMovement':  StockMovement.query.count(),
            'Sale':           Sale.query.count(),
            'ComboItem':      ComboItem.query.count(),
            'Combo':          Combo.query.count(),
        }

        print("📊 Registros actuales:")
        for nombre, cantidad in conteos_antes.items():
            print(f"   {nombre}: {cantidad}")

        if sum(conteos_antes.values()) == 0:
            print("\n✅ No hay nada para borrar.")
            return

        print("\n⚠️  Esto va a borrar TODOS los registros de arriba en PRODUCCIÓN.")
        print("   NO se tocan: Product, Category, User, StoreConfig, product_categories.")
        confirmacion = input("\nEscribí 'BORRAR' para confirmar: ")
        if confirmacion != 'BORRAR':
            print("Cancelado.")
            return

        try:
            borrados = {}
            borrados['SaleItem']      = SaleItem.query.delete(synchronize_session=False)
            borrados['StockMovement'] = StockMovement.query.delete(synchronize_session=False)
            borrados['Sale']          = Sale.query.delete(synchronize_session=False)
            borrados['ComboItem']     = ComboItem.query.delete(synchronize_session=False)
            borrados['Combo']         = Combo.query.delete(synchronize_session=False)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error durante el borrado, se hizo rollback: {e}")
            raise

        print("\n✅ Limpieza completada. Resumen:")
        for nombre, cantidad in borrados.items():
            print(f"   {nombre}: {cantidad} borrados")


if __name__ == '__main__':
    cleanup()
