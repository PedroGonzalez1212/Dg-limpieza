from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def home():
    return '<h1>DG Limpieza — Admin</h1>'