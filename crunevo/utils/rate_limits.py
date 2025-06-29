from functools import wraps
from flask_login import current_user


def smart_rate_limit(limit_key):
    """Rate limiting inteligente basado en usuario y acción"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated:
                # Usuarios verificados tienen límites más altos
                if current_user.verification_level >= 2:
                    limit = "50 per minute"
                else:
                    limit = "20 per minute"
            else:
                limit = "5 per minute"

            # Aplicar rate limit dinámicamente
            from crunevo.extensions import limiter

            limiter.limit(limit)(f)

            return f(*args, **kwargs)

        return decorated_function

    return decorator
