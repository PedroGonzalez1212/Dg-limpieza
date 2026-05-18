from flask import Blueprint

vendedor_bp = Blueprint('vendedor', __name__)

@vendedor_bp.route('/')
def home():
    return '<h1>DG Limpieza — Vendedor</h1>'