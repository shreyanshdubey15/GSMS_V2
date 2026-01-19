from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from ..utils.decorators import admin_or_employee_required
from config import Config

orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/<int:order_id>/invoice')
@login_required
def invoice(order_id):
    """Generate and display order invoice."""
    from ..models import Order, OrderItem  # Import inside function
    # Get order and verify access
    order = Order.query.get_or_404(order_id)

    # Check if user has permission to view this order
    if current_user.role == 'employee' and order.employee_id != current_user.id:
        abort(403)

    # Get order items
    order_items = OrderItem.query.filter_by(order_id=order_id)\
                                .order_by(OrderItem.product_name_snapshot)\
                                .all()

    # Auto-print if requested
    auto_print = 'print' in request.args

    return render_template('orders/invoice.html',
                         title=f'Invoice #{order.id}',
                         order=order,
                         order_items=order_items,
                         store_name=Config.STORE_NAME,
                         store_address=Config.STORE_ADDRESS,
                         store_phone=Config.STORE_PHONE,
                         store_email=Config.STORE_EMAIL,
                         auto_print=auto_print)