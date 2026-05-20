from functools import wraps
from flask import session, redirect, url_for, abort


def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if role and session.get('role') != role:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator