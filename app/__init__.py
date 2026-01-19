from flask import Flask, redirect, url_for
from flask_login import current_user
from config import Config
from extensions import migrate, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Import db here to avoid circular imports
    from .models import db

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # Root route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            # Redirect based on role
            from .models import User
            if current_user.is_admin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('employee.dashboard'))
        return redirect(url_for('auth.login'))

    # Register blueprints (import here to avoid circular imports)
    from .auth.routes import auth_bp
    from .admin.routes import admin_bp
    from .employee.routes import employee_bp
    from .orders.routes import orders_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(orders_bp, url_prefix='/orders')

    # Add CLI commands
    from .utils.cli import create_admin_command
    app.cli.add_command(create_admin_command)

    return app