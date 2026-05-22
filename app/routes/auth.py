from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → muestra el formulario
    POST → valida las credenciales y loguea al usuario

    Si el usuario ya está logueado, lo redirigimos directo al panel
    para que no vea el login innecesariamente.
    """
    if current_user.is_authenticated:
        return redirect(url_for('panel.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Buscamos el usuario por email en la DB
        user = User.query.filter_by(email=email, activo=True).first()

        if user and user.check_password(password):
            # login_user() de Flask-Login: guarda el usuario en la sesión
            # remember=True → cookie de 30 días, el usuario no tiene que
            # volver a loguearse si cierra el navegador
            login_user(user, remember=True)

            # Si venía de una página protegida, lo devolvemos ahí
            # (Flask-Login guarda la URL original en ?next=...)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('panel.dashboard'))

        # No decimos si el email o la contraseña están mal — por seguridad
        flash('Email o contraseña incorrectos.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Cierra la sesión del usuario y lo manda al home público.
    @login_required asegura que solo usuarios logueados puedan hacer logout.
    """
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('public.home'))