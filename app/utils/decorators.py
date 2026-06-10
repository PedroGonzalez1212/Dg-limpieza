from functools import wraps
from flask import abort
from flask_login import current_user


def vendedor_required(f):
    """
    Decorador para rutas que requieren rol 'vendedor' O 'admin'.
    
    ¿Por qué también permite admin? Porque el admin tiene TODOS los permisos
    del vendedor más los suyos propios. Sería raro que el admin no pueda
    usar el POS.
    
    Uso:
        @vendedor_required
        def mi_ruta():
            ...
    
    IMPORTANTE: Siempre usarlo DESPUÉS de @login_required, o usar junto
    con él. Si el usuario no está logueado, @login_required lo redirige
    al login antes de que lleguemos a verificar el rol.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.rol not in ('vendedor', 'admin'):
            # 403 = autenticado pero sin permiso (distinto de 401 = no logueado)
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorador para rutas que solo puede ver un admin.
    Uso: @admin_required encima de la función de ruta.
    Si el usuario no es admin, devuelve 403 Forbidden.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function