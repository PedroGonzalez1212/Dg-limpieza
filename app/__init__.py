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

    # Headers de seguridad HTTP. force_https=False en dev para no romper localhost.
    # Content Security Policy permisiva por ahora para no romper Cloudinary, Chart.js, etc.
    import os
    is_production = os.environ.get('FLASK_ENV') == 'production'
    Talisman(
        app,
        force_https=is_production,
        strict_transport_security=is_production,
        content_security_policy=False  # Lo activamos en una iteración futura
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

    return app
