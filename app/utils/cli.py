import click
from flask import current_app
from ..models import db
from app.models import User


@click.command('create-admin')
@click.option('--username', default=None, help='Admin username')
@click.option('--password', default=None, help='Admin password')
def create_admin_command(username, password):
    """Create an admin user."""

    # Use provided values or fall back to config
    admin_user = username or current_app.config['ADMIN_USER']
    admin_pass = password or current_app.config['ADMIN_PASS']

    # Check if admin already exists
    existing_admin = User.query.filter_by(username=admin_user).first()
    if existing_admin:
        if existing_admin.is_admin():
            click.echo(f'Admin user "{admin_user}" already exists.')
            return
        else:
            # Upgrade existing user to admin
            existing_admin.role = 'admin'
            db.session.commit()
            click.echo(f'User "{admin_user}" upgraded to admin role.')
            return

    # Create new admin user
    admin = User(username=admin_user, role='admin')
    admin.set_password(admin_pass)

    db.session.add(admin)
    db.session.commit()

    click.echo(f'Admin user "{admin_user}" created successfully.')