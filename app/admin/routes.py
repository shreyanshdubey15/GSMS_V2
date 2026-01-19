from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
from ..models import db
from .forms import ProductForm, EmployeeForm
from ..utils.decorators import admin_required
from ..utils.cloudinary_upload import upload_image, delete_image
from config import Config

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with key metrics and recent data."""
    from ..models import Product, Order, OrderItem, User  # Import inside function

    # Key metrics
    total_products = Product.query.count()
    total_employees = User.query.filter_by(role='employee').count()
    total_orders = Order.query.count()
    low_stock_count = Product.query.filter(Product.stock_qty <= 10).count()

    # Today's sales
    today = datetime.utcnow().date()
    today_orders = Order.query.filter(func.date(Order.created_at) == today).all()
    today_sales = float(sum(order.total_amount for order in today_orders))
    today_order_count = len(today_orders)

    # This month's sales
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_orders = Order.query.filter(Order.created_at >= month_start).all()
    month_sales = float(sum(order.total_amount for order in month_orders))
    month_order_count = len(month_orders)

    # This week's sales
    week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_orders = Order.query.filter(Order.created_at >= week_start).all()
    week_sales = float(sum(order.total_amount for order in week_orders))

    # Yesterday's sales for comparison
    yesterday = today - timedelta(days=1)
    yesterday_orders = Order.query.filter(func.date(Order.created_at) == yesterday).all()
    yesterday_sales = float(sum(order.total_amount for order in yesterday_orders))

    # Top selling products (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.line_total).label('total_revenue')
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= thirty_days_ago
    ).group_by(Product.id, Product.name).order_by(
        desc('total_quantity')
    ).limit(10).all()

    # Sales by category (last 30 days)
    category_sales = db.session.query(
        Product.category,
        func.sum(OrderItem.line_total).label('total_sales'),
        func.sum(OrderItem.quantity).label('total_quantity')
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= thirty_days_ago
    ).group_by(Product.category).order_by(
        desc('total_sales')
    ).all()

    # Recent orders (last 10)
    recent_orders = Order.query.order_by(desc(Order.created_at)).limit(10).all()

    # Low stock products (top 10 by stock quantity)
    low_stock_products = Product.query.filter(Product.stock_qty <= 10)\
                                    .order_by(Product.stock_qty).limit(10).all()

    # Out of stock products
    out_of_stock = Product.query.filter(Product.stock_qty == 0).count()

    # Top employees by sales (last 30 days)
    top_employees = db.session.query(
        User.username,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('total_sales')
    ).join(Order).filter(
        Order.created_at >= thirty_days_ago,
        User.role == 'employee'
    ).group_by(User.id, User.username).order_by(
        desc('total_sales')
    ).limit(5).all()

    # Inventory value calculation
    inventory_value = float(db.session.query(func.sum(Product.price * Product.stock_qty)).scalar() or 0)

    # Average order value
    avg_order_value = float(db.session.query(func.avg(Order.total_amount)).scalar() or 0)

    return render_template('admin/dashboard.html',
                         title='Admin Dashboard',
                         total_products=total_products,
                         total_employees=total_employees,
                         total_orders=total_orders,
                         low_stock_count=low_stock_count,
                         out_of_stock=out_of_stock,
                         today_sales=today_sales,
                         today_order_count=today_order_count,
                         yesterday_sales=yesterday_sales,
                         week_sales=week_sales,
                         month_sales=month_sales,
                         month_order_count=month_order_count,
                         top_products=top_products,
                         category_sales=category_sales,
                         top_employees=top_employees,
                         inventory_value=inventory_value,
                         avg_order_value=avg_order_value,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products)


@admin_bp.route('/api/sales')
@admin_required
def sales_api():
    """API endpoint for sales data (used by dashboard charts)."""
    from ..models import Order  # Import inside function
    days = int(request.args.get('days', 7))

    # Get sales data for the last N days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    sales_data = db.session.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.total_amount).label('total')
    ).filter(
        Order.created_at >= start_date
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    ).all()

    # Convert to dict format for Chart.js
    data = {
        'labels': [],
        'data': []
    }

    for row in sales_data:
        data['labels'].append(row.date.strftime('%Y-%m-%d'))
        data['data'].append(float(row.total))

    return jsonify(data)


# Product Management Routes
@admin_bp.route('/products')
@admin_required
def products():
    """List all products with search and pagination."""
    from ..models import Product  # Import inside function
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')

    query = Product.query

    if search:
        query = query.filter(
            or_(Product.name.ilike(f'%{search}%'),
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

    return render_template('admin/products_list.html',
                         title='Products',
                         products=products,
                         search=search,
                         category=category,
                         categories=[cat[0] for cat in categories])


@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def new_product():
    """Create a new product."""
    from ..models import Product  # Import inside function
    form = ProductForm()

    if form.validate_on_submit():
        # Handle image upload
        image_url = None
        if form.image.data:
            upload_result = upload_image(form.image.data)
            if 'error' in upload_result:
                flash(f'Image upload failed: {upload_result["error"]}', 'danger')
                return render_template('admin/product_form.html',
                                     title='New Product',
                                     form=form)

            image_url = upload_result['url']

        # Create product
        product = Product(
            name=form.name.data,
            price=form.price.data,
            stock_qty=form.stock_qty.data,
            category=form.category.data,
            image_url=image_url
        )

        db.session.add(product)
        db.session.commit()

        flash(f'Product "{product.name}" created successfully!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html',
                         title='New Product',
                         form=form)


@admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    """Edit an existing product."""
    from ..models import Product  # Import inside function
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)

    if form.validate_on_submit():
        # Handle image upload if new image provided
        if form.image.data:
            # Delete old image if exists
            if product.image_url:
                # Extract public_id from Cloudinary URL (this is simplified)
                # In a real app, you'd store the public_id separately
                pass

            upload_result = upload_image(form.image.data)
            if 'error' in upload_result:
                flash(f'Image upload failed: {upload_result["error"]}', 'danger')
                return render_template('admin/product_form.html',
                                     title=f'Edit {product.name}',
                                     form=form,
                                     product=product)

            product.image_url = upload_result['url']

        # Update product fields
        product.name = form.name.data
        product.price = form.price.data
        product.stock_qty = form.stock_qty.data
        product.category = form.category.data

        db.session.commit()

        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html',
                         title=f'Edit {product.name}',
                         form=form,
                         product=product)


@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@admin_required
def delete_product(id):
    """Delete a product."""
    from ..models import Product  # Import inside function
    product = Product.query.get_or_404(id)

    # Delete associated image
    if product.image_url:
        # Extract public_id and delete (simplified)
        pass

    db.session.delete(product)
    db.session.commit()

    flash(f'Product "{product.name}" deleted successfully!', 'success')
    return redirect(url_for('admin.products'))


# Employee Management Routes
@admin_bp.route('/employees')
@admin_required
def employees():
    """List all employees."""
    from ..models import User  # Import inside function
    employees = User.query.filter_by(role='employee').order_by(User.username).all()
    return render_template('admin/employees_list.html',
                         title='Employees',
                         employees=employees)


@admin_bp.route('/employees/new', methods=['GET', 'POST'])
@admin_required
def new_employee():
    """Create a new employee."""
    from ..models import User  # Import inside function
    form = EmployeeForm()

    if form.validate_on_submit():
        employee = User(
            username=form.username.data,
            role='employee'
        )
        employee.set_password(form.password.data)

        db.session.add(employee)
        db.session.commit()

        flash(f'Employee "{employee.username}" created successfully!', 'success')
        return redirect(url_for('admin.employees'))

    return render_template('admin/employee_form.html',
                         title='New Employee',
                         form=form)


@admin_bp.route('/employees/<int:id>/delete', methods=['POST'])
@admin_required
def delete_employee(id):
    """Delete an employee."""
    from ..models import User  # Import inside function
    employee = User.query.get_or_404(id)

    if employee.role != 'employee':
        flash('Cannot delete admin users.', 'danger')
        return redirect(url_for('admin.employees'))

    db.session.delete(employee)
    db.session.commit()

    flash(f'Employee "{employee.username}" deleted successfully!', 'success')
    return redirect(url_for('admin.employees'))


# Advanced Analytics and Reporting
@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Advanced analytics and reporting dashboard."""
    from ..models import Product, Order, OrderItem, User
    from datetime import datetime, timedelta
    from sqlalchemy import func, desc

    # Date range options
    end_date = datetime.utcnow()
    start_date_7d = end_date - timedelta(days=7)
    start_date_30d = end_date - timedelta(days=30)
    start_date_90d = end_date - timedelta(days=90)

    # Sales analytics
    sales_7d = db.session.query(func.sum(Order.total_amount)).filter(Order.created_at >= start_date_7d).scalar() or 0
    sales_30d = db.session.query(func.sum(Order.total_amount)).filter(Order.created_at >= start_date_30d).scalar() or 0
    sales_90d = db.session.query(func.sum(Order.total_amount)).filter(Order.created_at >= start_date_90d).scalar() or 0

    # Order analytics
    orders_7d = Order.query.filter(Order.created_at >= start_date_7d).count()
    orders_30d = Order.query.filter(Order.created_at >= start_date_30d).count()
    orders_90d = Order.query.filter(Order.created_at >= start_date_90d).count()

    # Product performance
    top_products_30d = db.session.query(
        Product.name, Product.category,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.line_total).label('total_revenue'),
        func.avg(OrderItem.unit_price_snapshot).label('avg_price')
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= start_date_30d
    ).group_by(Product.id, Product.name, Product.category).order_by(
        desc('total_revenue')
    ).limit(20).all()

    # Category performance
    category_performance = db.session.query(
        Product.category,
        func.count(func.distinct(Product.id)).label('product_count'),
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.line_total).label('total_revenue')
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= start_date_30d
    ).group_by(Product.category).order_by(
        desc('total_revenue')
    ).all()

    # Employee performance
    employee_performance = db.session.query(
        User.username,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('total_sales'),
        func.avg(Order.total_amount).label('avg_order_value')
    ).join(Order).filter(
        Order.created_at >= start_date_30d,
        User.role == 'employee'
    ).group_by(User.id, User.username).order_by(
        desc('total_sales')
    ).all()

    # Daily sales trend (last 30 days)
    daily_sales = []
    for i in range(30):
        day = end_date - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

        day_sales = db.session.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= day_start,
            Order.created_at <= day_end
        ).scalar() or 0

        daily_sales.append({
            'date': day.strftime('%Y-%m-%d'),
            'sales': float(day_sales)
        })

    daily_sales.reverse()

    return render_template('admin/analytics.html',
                         title='Analytics & Reports',
                         sales_7d=sales_7d,
                         sales_30d=sales_30d,
                         sales_90d=sales_90d,
                         orders_7d=orders_7d,
                         orders_30d=orders_30d,
                         orders_90d=orders_90d,
                         top_products=top_products_30d,
                         category_performance=category_performance,
                         employee_performance=employee_performance,
                         daily_sales=daily_sales)


@admin_bp.route('/inventory-report')
@admin_required
def inventory_report():
    """Comprehensive inventory report."""
    from ..models import Product
    from sqlalchemy import func

    # Inventory summary
    total_products = Product.query.count()
    in_stock = Product.query.filter(Product.stock_qty > 10).count()
    low_stock = Product.query.filter(Product.stock_qty.between(1, 10)).count()
    out_of_stock = Product.query.filter(Product.stock_qty == 0).count()

    # Inventory value
    inventory_value = float(db.session.query(func.sum(Product.price * Product.stock_qty)).scalar() or 0)

    # Products by category
    category_inventory = db.session.query(
        Product.category,
        func.count(Product.id).label('product_count'),
        func.sum(Product.stock_qty).label('total_stock'),
        func.sum(Product.price * Product.stock_qty).label('inventory_value')
    ).group_by(Product.category).order_by(desc('inventory_value')).all()

    # Low stock products (detailed)
    low_stock_products = Product.query.filter(Product.stock_qty <= 10)\
                                    .order_by(Product.stock_qty).all()

    # Top value products
    top_value_products = Product.query.order_by(desc(Product.price * Product.stock_qty)).limit(20).all()

    return render_template('admin/inventory_report.html',
                         title='Inventory Report',
                         total_products=total_products,
                         in_stock=in_stock,
                         low_stock=low_stock,
                         out_of_stock=out_of_stock,
                         inventory_value=inventory_value,
                         category_inventory=category_inventory,
                         low_stock_products=low_stock_products,
                         top_value_products=top_value_products)


@admin_bp.route('/sales-report')
@admin_required
def sales_report():
    """Comprehensive sales report."""
    from ..models import Order, OrderItem, Product, User
    from datetime import datetime, timedelta
    from sqlalchemy import func, desc, and_

    # Date ranges
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    this_week = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Sales by period
    today_sales = db.session.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) == today
    ).scalar() or 0

    yesterday_sales = db.session.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) == yesterday
    ).scalar() or 0

    week_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= this_week
    ).scalar() or 0

    month_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= this_month
    ).scalar() or 0

    # Order statistics
    today_orders = Order.query.filter(func.date(Order.created_at) == today).count()
    week_orders = Order.query.filter(Order.created_at >= this_week).count()
    month_orders = Order.query.filter(Order.created_at >= this_month).count()

    # Payment method breakdown
    payment_methods = db.session.query(
        Order.payment_method,
        func.count(Order.id).label('count'),
        func.sum(Order.total_amount).label('total')
    ).group_by(Order.payment_method).all()

    # Hourly sales pattern (today)
    hourly_sales = []
    for hour in range(24):
        hour_start = datetime.utcnow().replace(hour=hour, minute=0, second=0, microsecond=0)
        hour_end = hour_start.replace(hour=hour, minute=59, second=59, microsecond=999999)

        hour_total = db.session.query(func.sum(Order.total_amount)).filter(
            and_(Order.created_at >= hour_start, Order.created_at <= hour_end)
        ).scalar() or 0

        hourly_sales.append({
            'hour': hour,
            'sales': float(hour_total)
        })

    # Top customers (by order frequency)
    top_customers = db.session.query(
        User.username,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('total_spent'),
        func.avg(Order.total_amount).label('avg_order')
    ).join(Order).filter(User.role == 'employee').group_by(User.id, User.username)\
     .order_by(desc('order_count')).limit(10).all()

    return render_template('admin/sales_report.html',
                         title='Sales Report',
                         today_sales=today_sales,
                         yesterday_sales=yesterday_sales,
                         week_sales=week_sales,
                         month_sales=month_sales,
                         today_orders=today_orders,
                         week_orders=week_orders,
                         month_orders=month_orders,
                         payment_methods=payment_methods,
                         hourly_sales=hourly_sales,
                         top_customers=top_customers)


@admin_bp.route('/backup')
@admin_required
def backup():
    """Data backup and export functionality."""
    from ..models import Product, Order, OrderItem, User
    import json
    from datetime import datetime

    # Get all data
    products = Product.query.all()
    orders = Order.query.all()
    order_items = OrderItem.query.all()
    users = User.query.all()

    # Prepare backup data
    backup_data = {
        'metadata': {
            'created_at': datetime.utcnow().isoformat(),
            'version': '1.0',
            'total_products': len(products),
            'total_orders': len(orders),
            'total_users': len(users)
        },
        'products': [
            {
                'id': p.id,
                'name': p.name,
                'price': float(p.price),
                'stock_qty': p.stock_qty,
                'category': p.category,
                'image_url': p.image_url,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None
            } for p in products
        ],
        'users': [
            {
                'id': u.id,
                'username': u.username,
                'role': u.role,
                'created_at': u.created_at.isoformat() if u.created_at else None
            } for u in users
        ],
        'orders': [
            {
                'id': o.id,
                'employee_id': o.employee_id,
                'total_amount': float(o.total_amount),
                'tax_amount': float(o.tax_amount),
                'discount_amount': float(o.discount_amount),
                'payment_method': o.payment_method,
                'status': o.status,
                'created_at': o.created_at.isoformat() if o.created_at else None
            } for o in orders
        ],
        'order_items': [
            {
                'id': oi.id,
                'order_id': oi.order_id,
                'product_id': oi.product_id,
                'product_name_snapshot': oi.product_name_snapshot,
                'unit_price_snapshot': float(oi.unit_price_snapshot),
                'quantity': oi.quantity,
                'line_total': float(oi.line_total)
            } for oi in order_items
        ]
    }

    # Convert to JSON for display/download
    backup_json = json.dumps(backup_data, indent=2)

    return render_template('admin/backup.html',
                         title='Data Backup',
                         backup_data=backup_data,
                         backup_json=backup_json)


@admin_bp.route('/settings')
@admin_required
def settings():
    """System settings and configuration."""
    return render_template('admin/settings.html',
                         title='System Settings')


@admin_bp.route('/export-data')
@admin_required
def export_data():
    """Export data in various formats."""
    from ..models import Product, Order, OrderItem, User
    import csv
    import io
    from flask import Response
    from datetime import datetime

    # Get export format from query parameter
    export_format = request.args.get('format', 'csv')

    if export_format == 'csv':
        # Create CSV response
        output = io.StringIO()
        writer = csv.writer(output)

        # Products export
        products = Product.query.all()
        writer.writerow(['Products'])
        writer.writerow(['ID', 'Name', 'Price', 'Stock', 'Category', 'Created'])
        for product in products:
            writer.writerow([
                product.id,
                product.name,
                float(product.price),
                product.stock_qty,
                product.category,
                product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else ''
            ])

        writer.writerow([])
        writer.writerow(['Orders'])
        writer.writerow(['ID', 'Employee', 'Total', 'Payment Method', 'Status', 'Created'])
        orders = Order.query.all()
        for order in orders:
            writer.writerow([
                order.id,
                order.employee.username if order.employee else '',
                float(order.total_amount),
                order.payment_method,
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else ''
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=grocery_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )

    return render_template('admin/export_data.html', title='Export Data')


@admin_bp.route('/bulk-import', methods=['GET', 'POST'])
@admin_required
def bulk_import():
    """Bulk import products from CSV."""
    from flask import request, flash, redirect
    import csv
    import io
    from ..models import Product, db

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV file
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)

                imported_count = 0
                errors = []

                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        # Validate required fields
                        if not all(key in row for key in ['name', 'price', 'stock_qty', 'category']):
                            errors.append(f"Row {row_num}: Missing required fields")
                            continue

                        # Create product
                        product = Product(
                            name=row['name'].strip(),
                            price=float(row['price']),
                            stock_qty=int(row['stock_qty']),
                            category=row['category'].strip(),
                            image_url=row.get('image_url', '').strip() or None
                        )

                        db.session.add(product)
                        imported_count += 1

                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")

                db.session.commit()

                if imported_count > 0:
                    flash(f'Successfully imported {imported_count} products', 'success')
                if errors:
                    flash(f'Errors encountered: {" | ".join(errors[:5])}', 'warning')

            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                db.session.rollback()

        else:
            flash('Please upload a valid CSV file', 'error')

    return render_template('admin/bulk_import.html', title='Bulk Import')


@admin_bp.route('/system-health')
@admin_required
def system_health():
    """System health monitoring and diagnostics."""
    try:
        import psutil
    except ImportError:
        psutil = None

    import os
    from ..models import Product, Order, User

    # Database health
    db_stats = {
        'total_products': Product.query.count(),
        'total_orders': Order.query.count(),
        'total_users': User.query.count(),
        'db_size_mb': round((Product.query.count() * 0.1 + Order.query.count() * 0.05 + User.query.count() * 0.01), 2)
    }

    # System health
    if psutil:
        system_stats = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': round(psutil.virtual_memory().used / (1024**3), 2),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'disk_used_gb': round(psutil.disk_usage('/').used / (1024**3), 2),
            'disk_total_gb': round(psutil.disk_usage('/').total / (1024**3), 2)
        }
    else:
        system_stats = {
            'cpu_percent': 'N/A',
            'memory_percent': 'N/A',
            'memory_used_gb': 'N/A',
            'memory_total_gb': 'N/A',
            'disk_usage_percent': 'N/A',
            'disk_used_gb': 'N/A',
            'disk_total_gb': 'N/A'
        }

    # Application health
    app_health = {
        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        'uptime': 'Running',
        'last_backup': 'Today',
        'active_connections': 1
    }

    return render_template('admin/system_health.html',
                         title='System Health',
                         db_stats=db_stats,
                         system_stats=system_stats,
                         app_health=app_health)


@admin_bp.route('/profit-analysis')
@admin_required
def profit_analysis():
    """Profit analysis and financial reporting."""
    from ..models import Order, OrderItem, Product
    from datetime import datetime, timedelta
    from sqlalchemy import func, desc
    from decimal import Decimal

    # Assume cost price is 70% of selling price (configurable)
    COST_MARGIN = Decimal('0.7')

    # Calculate profits for different periods
    periods = {
        'today': datetime.utcnow().date(),
        'this_week': datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()),
        'this_month': datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        'last_30_days': datetime.utcnow() - timedelta(days=30),
        'last_90_days': datetime.utcnow() - timedelta(days=90)
    }

    profit_data = {}
    for period_name, start_date in periods.items():
        if period_name == 'today':
            # For today, filter by date
            orders = Order.query.filter(func.date(Order.created_at) == start_date).all()
        else:
            # For other periods, filter by datetime
            orders = Order.query.filter(Order.created_at >= start_date).all()

        total_revenue = sum(order.total_amount for order in orders)
        total_cost = sum(
            sum(item.quantity * (item.unit_price_snapshot * COST_MARGIN) for item in order.order_items)
            for order in orders
        )
        total_profit = total_revenue - total_cost
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

        profit_data[period_name] = {
            'revenue': float(total_revenue),
            'cost': float(total_cost),
            'profit': float(total_profit),
            'margin': float(profit_margin),
            'orders': len(orders)
        }

    # Top profitable products
    top_profitable_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('total_sold'),
        func.sum(OrderItem.line_total).label('total_revenue'),
        (func.sum(OrderItem.line_total) - func.sum(OrderItem.quantity * OrderItem.unit_price_snapshot * COST_MARGIN)).label('total_profit')
    ).join(OrderItem).join(Order).filter(
        Order.created_at >= periods['last_30_days']
    ).group_by(Product.id, Product.name).order_by(
        desc('total_profit')
    ).limit(20).all()

    # Profit trend (daily for last 30 days)
    profit_trend = []
    for i in range(30):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)

        day_orders = Order.query.filter(
            Order.created_at >= day_start,
            Order.created_at <= day_end
        ).all()

        day_revenue = sum(order.total_amount for order in day_orders)
        day_cost = sum(
            sum(item.quantity * (item.unit_price_snapshot * COST_MARGIN) for item in order.order_items)
            for order in day_orders
        )

        profit_trend.append({
            'date': day.strftime('%Y-%m-%d'),
            'profit': float(day_revenue - day_cost)
        })

    profit_trend.reverse()

    return render_template('admin/profit_analysis.html',
                         title='Profit Analysis',
                         profit_data=profit_data,
                         top_profitable_products=top_profitable_products,
                         profit_trend=profit_trend,
                         cost_margin=float(COST_MARGIN * 100))


# Additional Admin Features
@admin_bp.route('/customers')
@admin_required
def customers():
    """Customer management and analytics."""
    from ..models import Order, User
    from datetime import datetime, timedelta
    from sqlalchemy import func, desc

    # Customer analytics
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # Top customers by spending
    top_customers_by_spending = db.session.query(
        User.username,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('total_spent'),
        func.avg(Order.total_amount).label('avg_order_value'),
        func.max(Order.created_at).label('last_order_date')
    ).join(Order).filter(
        Order.created_at >= thirty_days_ago,
        User.role == 'employee'
    ).group_by(User.id, User.username).order_by(
        desc('total_spent')
    ).limit(20).all()

    # Customer lifetime value
    customer_lifetime_value = db.session.query(
        User.username,
        func.sum(Order.total_amount).label('lifetime_value'),
        func.count(Order.id).label('total_orders'),
        func.min(Order.created_at).label('first_order'),
        func.max(Order.created_at).label('last_order')
    ).join(Order).filter(User.role == 'employee').group_by(User.id, User.username).order_by(
        desc('lifetime_value')
    ).all()

    # Customer retention (active in last 30 days)
    active_customers = db.session.query(User).filter(
        User.role == 'employee',
        User.id.in_(
            db.session.query(Order.employee_id).filter(
                Order.created_at >= thirty_days_ago
            ).distinct()
        )
    ).all()

    # Customer segments
    vip_customers = [c for c in customer_lifetime_value if c.lifetime_value >= 1000]
    regular_customers = [c for c in customer_lifetime_value if 500 <= c.lifetime_value < 1000]
    new_customers = [c for c in customer_lifetime_value if c.lifetime_value < 500]

    return render_template('admin/customers.html',
                         title='Customer Management',
                         top_customers=top_customers_by_spending,
                         customer_lifetime=customer_lifetime_value,
                         active_customers=active_customers,
                         vip_customers=vip_customers,
                         regular_customers=regular_customers,
                         new_customers=new_customers)


@admin_bp.route('/suppliers')
@admin_required
def suppliers():
    """Supplier/vendor management."""
    # Mock supplier data - in a real app, this would be a database table
    suppliers = [
        {
            'id': 1,
            'name': 'Fresh Farms Co.',
            'category': 'Fruits & Vegetables',
            'contact': 'john@freshfarms.com',
            'phone': '(555) 123-4567',
            'rating': 4.8,
            'total_orders': 145,
            'total_value': 12500.50,
            'last_order': '2024-01-20',
            'status': 'Active'
        },
        {
            'id': 2,
            'name': 'Dairy Best Ltd.',
            'category': 'Dairy Products',
            'contact': 'sarah@dairybest.com',
            'phone': '(555) 234-5678',
            'rating': 4.6,
            'total_orders': 89,
            'total_value': 8750.25,
            'last_order': '2024-01-19',
            'status': 'Active'
        },
        {
            'id': 3,
            'name': 'Bakery Masters',
            'category': 'Bakery',
            'contact': 'mike@bakerymasters.com',
            'phone': '(555) 345-6789',
            'rating': 4.9,
            'total_orders': 67,
            'total_value': 5420.75,
            'last_order': '2024-01-18',
            'status': 'Active'
        },
        {
            'id': 4,
            'name': 'Meat & Poultry Inc.',
            'category': 'Meat',
            'contact': 'lisa@meatpoultry.com',
            'phone': '(555) 456-7890',
            'rating': 4.7,
            'total_orders': 52,
            'total_value': 8900.00,
            'last_order': '2024-01-17',
            'status': 'Inactive'
        }
    ]

    # Supplier performance metrics
    total_suppliers = len(suppliers)
    active_suppliers = len([s for s in suppliers if s['status'] == 'Active'])
    avg_rating = sum(s['rating'] for s in suppliers) / len(suppliers)
    total_supplier_value = sum(s['total_value'] for s in suppliers)

    return render_template('admin/suppliers.html',
                         title='Supplier Management',
                         suppliers=suppliers,
                         total_suppliers=total_suppliers,
                         active_suppliers=active_suppliers,
                         avg_rating=round(avg_rating, 1),
                         total_supplier_value=total_supplier_value)


@admin_bp.route('/notifications')
@admin_required
def notifications():
    """Notification center and alerts management."""
    # Mock notifications - in a real app, this would be stored in database
    notifications_list = [
        {
            'id': 1,
            'type': 'warning',
            'title': 'Low Stock Alert',
            'message': 'Apple (Red) has only 5 items remaining',
            'timestamp': '2024-01-20 10:30:00',
            'read': False,
            'action_url': '/admin/products'
        },
        {
            'id': 2,
            'type': 'info',
            'title': 'New Order Received',
            'message': 'Order #1234 has been placed by customer John Doe',
            'timestamp': '2024-01-20 09:15:00',
            'read': True,
            'action_url': '/admin/orders'
        },
        {
            'id': 3,
            'type': 'success',
            'title': 'Payment Processed',
            'message': 'Payment of $45.67 for Order #1233 has been processed',
            'timestamp': '2024-01-20 08:45:00',
            'read': True,
            'action_url': '/admin/orders'
        },
        {
            'id': 4,
            'type': 'danger',
            'title': 'System Alert',
            'message': 'Database backup failed. Please check system logs.',
            'timestamp': '2024-01-19 23:00:00',
            'read': False,
            'action_url': '/admin/system-health'
        },
        {
            'id': 5,
            'type': 'info',
            'title': 'Monthly Report Ready',
            'message': 'Your monthly sales report for December 2024 is now available',
            'timestamp': '2024-01-19 22:30:00',
            'read': False,
            'action_url': '/admin/sales-report'
        }
    ]

    # Notification statistics
    total_notifications = len(notifications_list)
    unread_notifications = len([n for n in notifications_list if not n['read']])
    critical_alerts = len([n for n in notifications_list if n['type'] == 'danger' and not n['read']])

    return render_template('admin/notifications.html',
                         title='Notifications',
                         notifications=notifications_list,
                         total_notifications=total_notifications,
                         unread_notifications=unread_notifications,
                         critical_alerts=critical_alerts)


@admin_bp.route('/reports')
@admin_required
def reports():
    """Comprehensive reporting dashboard."""
    return render_template('admin/reports.html', title='Reports')


@admin_bp.route('/user-management')
@admin_required
def user_management():
    """User and role management."""
    from ..models import User

    users = User.query.all()
    admin_count = User.query.filter_by(role='admin').count()
    employee_count = User.query.filter_by(role='employee').count()

    return render_template('admin/user_management.html',
                         title='User Management',
                         users=users,
                         admin_count=admin_count,
                         employee_count=employee_count)


@admin_bp.route('/audit-log')
@admin_required
def audit_log():
    """System audit log and activity tracking."""
    # Mock audit log data
    audit_entries = [
        {
            'timestamp': '2024-01-20 10:30:15',
            'user': 'admin',
            'action': 'LOGIN',
            'resource': 'System',
            'details': 'Successful login from 192.168.1.100',
            'ip_address': '192.168.1.100'
        },
        {
            'timestamp': '2024-01-20 10:25:42',
            'user': 'admin',
            'action': 'UPDATE',
            'resource': 'Product',
            'details': 'Updated price for Apple (Red)',
            'ip_address': '192.168.1.100'
        },
        {
            'timestamp': '2024-01-20 10:20:18',
            'user': 'john_doe',
            'action': 'CREATE',
            'resource': 'Order',
            'details': 'Created order #1234',
            'ip_address': '192.168.1.101'
        },
        {
            'timestamp': '2024-01-20 10:15:33',
            'user': 'admin',
            'action': 'DELETE',
            'resource': 'Product',
            'details': 'Deleted expired product: Old Bread',
            'ip_address': '192.168.1.100'
        },
        {
            'timestamp': '2024-01-20 09:45:12',
            'user': 'jane_smith',
            'action': 'UPDATE',
            'resource': 'Employee',
            'details': 'Updated contact information',
            'ip_address': '192.168.1.102'
        }
    ]

    return render_template('admin/audit_log.html',
                         title='Audit Log',
                         audit_entries=audit_entries)


@admin_bp.route('/maintenance')
@admin_required
def maintenance():
    """System maintenance and optimization tools."""
    return render_template('admin/maintenance.html', title='Maintenance')


# Order Management Routes
@admin_bp.route('/theme-test')
@admin_required
def theme_test():
    """Test page for dark mode functionality."""
    return render_template('admin/theme_test.html', title='Theme Test')


@admin_bp.route('/orders')
@admin_required
def orders():
    """List all orders with filters."""
    from ..models import Order, User  # Import inside function
    page = request.args.get('page', 1, type=int)
    employee_filter = request.args.get('employee', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Order.query.join(User)

    if employee_filter:
        query = query.filter(User.username.ilike(f'%{employee_filter}%'))

    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Order.created_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(Order.created_at <= end)
        except ValueError:
            pass

    orders = query.order_by(desc(Order.created_at))\
                 .paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)

    return render_template('admin/orders_list.html',
                         title='Orders',
                         orders=orders,
                         employee_filter=employee_filter,
                         start_date=start_date,
                         end_date=end_date)