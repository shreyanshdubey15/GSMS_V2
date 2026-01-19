from app import create_app
from app.models import Order, Product, User, db
from datetime import datetime, timedelta
from sqlalchemy import func

app = create_app()
with app.app_context():
    print('=== DATABASE STATUS ===')
    print(f'Orders count: {Order.query.count()}')
    print(f'Products count: {Product.query.count()}')
    print(f'Users count: {User.query.count()}')

    print('\n=== SAMPLE DATA ===')
    if Order.query.count() > 0:
        orders = Order.query.limit(3).all()
        for order in orders:
            print(f'Order {order.id}: ${order.total_amount} by {order.employee.username if order.employee else "Unknown"} at {order.created_at}')
    else:
        print('No orders found in database')

    if Product.query.count() > 0:
        products = Product.query.limit(3).all()
        for product in products:
            print(f'Product {product.id}: {product.name} - ${product.price} (Stock: {product.stock_qty})')
    else:
        print('No products found in database')

    print('\n=== DATE CALCULATIONS ===')
    today = datetime.utcnow().date()
    week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    print(f'Today: {today}')
    print(f'Week start: {week_start}')

    today_orders = Order.query.filter(func.date(Order.created_at) == today).count()
    week_orders = Order.query.filter(Order.created_at >= week_start).count()

    print(f'Orders today: {today_orders}')
    print(f'Orders this week: {week_orders}')

    print('\n=== SALES CALCULATIONS ===')
    # Test the sales calculations
    today_sales = db.session.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) == today
    ).scalar() or 0

    week_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= week_start
    ).scalar() or 0

    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= month_start
    ).scalar() or 0

    print(f'Today sales: ${today_sales} (type: {type(today_sales)})')
    print(f'Week sales: ${week_sales} (type: {type(week_sales)})')
    print(f'Month sales: ${month_sales} (type: {type(month_sales)})')

    # Test inventory value calculation
    inventory_value = db.session.query(func.sum(Product.price * Product.stock_qty)).scalar() or 0
    print(f'Inventory value: ${inventory_value} (type: {type(inventory_value)})')

    # Test avg order value
    avg_order_value = db.session.query(func.avg(Order.total_amount)).scalar() or 0
    print(f'Avg order value: ${avg_order_value} (type: {type(avg_order_value)})')