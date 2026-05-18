from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    return '<h1>DG Limpieza — Auth</h1>'