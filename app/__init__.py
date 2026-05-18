from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config

# Instancias de extensiones (sin app todavía)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Conectar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Configurar login
    login_manager.login_view = 'auth.login'  # Ruta del login
    login_manager.login_message = 'Necesitás iniciar sesión para acceder.'

    # Registrar blueprints (grupos de rutas)
    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.vendedor import vendedor_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(vendedor_bp, url_prefix='/vendedor')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    return app