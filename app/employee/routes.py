from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from ..models import db
from .forms import AddToCartForm, UpdateCartForm, CheckoutForm
from ..utils.decorators import employee_required
from ..utils.helpers import (get_cart, add_to_cart, update_cart_item, remove_from_cart,
                          clear_cart, get_cart_total, calculate_tax, validate_cart_stock)
from config import Config
from decimal import Decimal

employee_bp = Blueprint('employee', __name__)


@employee_bp.route('/dashboard')
@employee_required
def dashboard():
    """Employee dashboard with quick access and recent orders."""
    from ..models import Order  # type: ignore[attr-defined]  # Import inside function
    # Recent orders for this employee (last 5)
    recent_orders = Order.query.filter_by(employee_id=current_user.id)\
                             .order_by(Order.created_at.desc())\
                             .limit(5)\
                             .all()

    return render_template('employee/dashboard.html',
                         title='Employee Dashboard',
                         recent_orders=recent_orders)


@employee_bp.route('/products')
@employee_required
def products():
    from ..models import Product  # type: ignore[attr-defined]  # Import inside function
    """Browse products with search functionality."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')

    query = Product.query.filter(Product.stock_qty > 0)  # Only show products in stock

    if search:
        query = query.filter(
            or_(Product.name.ilike(f'%{search}%'),
                Product.id.ilike(f'%{search}%'),
                Product.category.ilike(f'%{search}%'))
        )

    if category:
        query = query.filter(Product.category == category)

    products = query.order_by(Product.name)\
                   .paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)

    categories = db.session.query(Product.category)\
                         .distinct()\
                         .order_by(Product.category)\
                         .all()

    # Add cart form for each product
    cart_forms = {}
    for product in products.items:
        form = AddToCartForm()
        form.submit.label.text = f'Add {product.name} to Cart'
        cart_forms[product.id] = form

    return render_template('employee/products_list.html',
                         title='Products',
                         products=products,
                         search=search,
                         category=category,
                         categories=[cat[0] for cat in categories],
                         cart_forms=cart_forms)


@employee_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@employee_required
def add_to_cart_route(product_id):
    """Add product to cart."""
    from ..models import Product  # type: ignore[attr-defined]  # Import inside function
    product = Product.query.get_or_404(product_id)

    if product.stock_qty <= 0:
        flash(f'Sorry, {product.name} is out of stock.', 'warning')
        return redirect(url_for('employee.products'))

    form = AddToCartForm()
    if form.validate_on_submit():
        add_to_cart(product_id, form.quantity.data)
        flash(f'Added {form.quantity.data} x {product.name} to cart.', 'success')
    else:
        flash('Invalid quantity.', 'danger')

    return redirect(url_for('employee.products'))


@employee_bp.route('/cart', methods=['GET', 'POST'])
@employee_required
def cart():
    """View and manage cart."""
    from ..models import Product  # type: ignore[attr-defined]  # Import inside function
    cart_data = get_cart()
    cart_items = []
    total = Decimal('0.00')

    if cart_data:
        # Get products for cart items
        product_ids = list(cart_data.keys())
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        products_dict = {str(p.id): p for p in products}

        for product_id, quantity in cart_data.items():
            product = products_dict.get(product_id)
            if product:
                line_total = product.price * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'line_total': line_total
                })
                total += line_total

        # Sort cart items by product name
        cart_items.sort(key=lambda x: x['product'].name)

    # Handle cart updates
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update':
            for item in cart_items:
                quantity_field = f'quantity_{item["product"].id}'
                new_quantity = request.form.get(quantity_field, type=int)

                if new_quantity is not None:
                    if new_quantity <= 0:
                        remove_from_cart(item['product'].id)
                        flash(f'Removed {item["product"].name} from cart.', 'info')
                    elif new_quantity != item['quantity']:
                        if new_quantity > item['product'].stock_qty:
                            flash(f'Cannot update {item["product"].name}. Only {item["product"].stock_qty} in stock.', 'warning')
                        else:
                            update_cart_item(item['product'].id, new_quantity)
                            flash(f'Updated {item["product"].name} quantity to {new_quantity}.', 'success')

        elif action == 'remove':
            product_id = request.form.get('product_id', type=int)
            if product_id:
                product = products_dict.get(str(product_id))
                if product:
                    remove_from_cart(product_id)
                    flash(f'Removed {product.name} from cart.', 'info')

        elif action == 'clear':
            clear_cart()
            flash('Cart cleared.', 'info')

        return redirect(url_for('employee.cart'))

    tax = calculate_tax(total)
    grand_total = total + tax

    return render_template('employee/cart.html',
                         title='Shopping Cart',
                         cart_items=cart_items,
                         total=total,
                         tax=tax,
                         grand_total=grand_total)


@employee_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
@employee_required
def remove_from_cart_route(product_id):
    """Remove item from cart."""
    from ..models import Product  # type: ignore[attr-defined]  # Import inside function
    product = Product.query.get(product_id)
    if product:
        remove_from_cart(product_id)
        flash(f'Removed {product.name} from cart.', 'info')
    else:
        remove_from_cart(product_id)

    return redirect(url_for('employee.cart'))


@employee_bp.route('/cart/clear', methods=['POST'])
@employee_required
def clear_cart_route():
    """Clear entire cart."""
    clear_cart()
    flash('Cart cleared.', 'info')
    return redirect(url_for('employee.cart'))


@employee_bp.route('/checkout', methods=['GET', 'POST'])
@employee_required
def checkout():
    """Checkout process."""
    from ..models import Product, Order, OrderItem  # type: ignore[attr-defined]  # Import inside function
    cart_data = get_cart()

    if not cart_data:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('employee.products'))

    # Get cart items with validation
    product_ids = list(cart_data.keys())
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    products_dict = {str(p.id): p for p in products}

    cart_items = []
    subtotal = Decimal('0.00')

    for product_id, quantity in cart_data.items():
        product = products_dict.get(product_id)
        if product:
            line_total = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'line_total': line_total
            })
            subtotal += line_total

    # Validate stock availability
    stock_validation = validate_cart_stock(cart_data, [item['product'] for item in cart_items])
    if not stock_validation['valid']:
        for error in stock_validation['errors']:
            flash(error, 'danger')
        return redirect(url_for('employee.cart'))

    tax = calculate_tax(subtotal)
    total = subtotal + tax

    form = CheckoutForm()

    if form.validate_on_submit():
        try:
            # Create order in transaction
            with db.session.begin():
                # Create order
                order = Order(
                    employee_id=current_user.id,
                    total_amount=total,
                    tax_amount=tax,
                    discount_amount=Decimal('0.00'),
                    payment_method=form.payment_method.data
                )
                db.session.add(order)
                db.session.flush()  # Get order ID

                # Create order items and update stock
                for item in cart_items:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item['product'].id,
                        product_name_snapshot=item['product'].name,
                        unit_price_snapshot=item['product'].price,
                        quantity=item['quantity'],
                        line_total=item['line_total']
                    )
                    db.session.add(order_item)

                    # Update product stock
                    item['product'].stock_qty -= item['quantity']

                # Clear cart
                clear_cart()

            flash(f'Order #{order.id} completed successfully!', 'success')
            return redirect(url_for('employee.orders'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing your order. Please try again.', 'danger')
            current_app.logger.error(f'Checkout error: {str(e)}')

    return render_template('employee/checkout.html',
                         title='Checkout',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         tax=tax,
                         total=total,
                         form=form)


@employee_bp.route('/orders')
@employee_required
def orders():
    """View employee's order history."""
    from ..models import Order  # type: ignore[attr-defined]  # Import inside function
    page = request.args.get('page', 1, type=int)

    orders = Order.query.filter_by(employee_id=current_user.id)\
                       .order_by(Order.created_at.desc())\
                       .paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)

    return render_template('employee/orders_list.html',
                         title='My Orders',
                         orders=orders)