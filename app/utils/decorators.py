from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user


def roles_required(*roles):
    """Decorator to require specific roles for a route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('auth.login'))

            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin role."""
    return roles_required('admin')(f)


def employee_required(f):
    """Decorator to require employee role."""
    return roles_required('employee')(f)


def admin_or_employee_required(f):
    """Decorator to require either admin or employee role."""
    return roles_required('admin', 'employee')(f)