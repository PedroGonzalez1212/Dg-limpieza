from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    csrf.init_app(app)

    import os
    is_production = os.environ.get('FLASK_ENV') == 'production'

    csp = {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            "https://unpkg.com",
            "https://fonts.googleapis.com",
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "https://fonts.googleapis.com",
        ],
        'font-src': ["'self'", "https://fonts.gstatic.com"],
        'img-src': ["'self'", "https://res.cloudinary.com", "data:", "https://www.google.com"],
        'frame-src': ["https://www.google.com"],
        'connect-src': ["'self'"],
    }

    Talisman(
        app,
        force_https=is_production,
        strict_transport_security=is_production,
        content_security_policy=csp,
        content_security_policy_report_only=not is_production,
    )

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Necesitás iniciar sesión para acceder.'

    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.vendedor import vendedor_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(vendedor_bp, url_prefix='/panel', name='panel')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500

    return app
