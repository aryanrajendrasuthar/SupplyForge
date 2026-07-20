from functools import wraps

from flask import current_app, g, jsonify, request

from supplyforge_auth.cookies import SESSION_COOKIE_NAME


def require_session(role: str | None = None):
    """Gates a Flask view on a valid session cookie, optionally requiring a role.

    "admin" always satisfies any role check — a deliberate simplification
    instead of a full role-hierarchy system, which this project doesn't
    need yet.

    Reads the session store off `current_app.session_store` (each service
    wires its own Redis connection at app-factory time) rather than taking
    the store as a decorator argument, since decorators run at import time,
    before any app context exists.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            token = request.cookies.get(SESSION_COOKIE_NAME)
            session_data = current_app.session_store.resolve(token) if token else None
            if session_data is None:
                return jsonify({"error": "authentication required"}), 401
            user_role = session_data.get("role")
            if role is not None and user_role != role and user_role != "admin":
                return jsonify({"error": "forbidden"}), 403
            g.current_user = session_data
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
