from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app.models import User
from app import limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Máximo 5 intentos por IP por minuto
def login():
    if current_user.is_authenticated:
        return redirect(url_for('panel.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email, activo=True).first()

        if user and user.check_password(password):
            login_user(user, remember=True)

            next_page = request.args.get('next')
            # Validamos que el redirect sea interno (no a otro dominio)
            if next_page:
                parsed = urlparse(next_page)
                if parsed.netloc != '':  # tiene dominio externo → ignorar
                    next_page = None

            return redirect(next_page or url_for('panel.dashboard'))

        flash('Email o contraseña incorrectos.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('public.home'))
