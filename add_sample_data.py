from app import create_app
from app.models import Order, OrderItem, Product, User, db
from datetime import datetime, timedelta
from decimal import Decimal
import random

app = create_app()
with app.app_context():
    print("Adding sample data to database...")

    # Check if we already have data
    if Product.query.count() > 0:
        print("Sample data already exists. Skipping...")
        exit()

    # Create sample products
    products_data = [
        {"name": "Apple (Red)", "price": 2.50, "stock_qty": 100, "category": "Fruits"},
        {"name": "Banana", "price": 1.99, "stock_qty": 150, "category": "Fruits"},
        {"name": "Milk (1L)", "price": 3.99, "stock_qty": 50, "category": "Dairy"},
        {"name": "Bread (Whole Wheat)", "price": 2.99, "stock_qty": 75, "category": "Bakery"},
        {"name": "Eggs (Dozen)", "price": 4.99, "stock_qty": 30, "category": "Dairy"},
        {"name": "Chicken Breast (1kg)", "price": 8.99, "stock_qty": 25, "category": "Meat"},
        {"name": "Rice (5kg)", "price": 12.99, "stock_qty": 20, "category": "Grains"},
        {"name": "Tomatoes", "price": 3.49, "stock_qty": 80, "category": "Vegetables"},
        {"name": "Potatoes (5kg)", "price": 4.99, "stock_qty": 40, "category": "Vegetables"},
        {"name": "Orange Juice (1L)", "price": 4.49, "stock_qty": 35, "category": "Beverages"}
    ]

    products = []
    for product_data in products_data:
        product = Product(
            name=product_data["name"],
            price=Decimal(str(product_data["price"])),
            stock_qty=product_data["stock_qty"],
            category=product_data["category"]
        )
        db.session.add(product)
        products.append(product)

    db.session.commit()
    print(f"Added {len(products)} products")

    # Get users (assuming admin and some employees exist)
    users = User.query.filter_by(role='employee').all()
    if not users:
        # Create a sample employee if none exist
        employee = User(username='john_doe', role='employee')
        employee.set_password('password')
        db.session.add(employee)
        users = [employee]
        db.session.commit()

    # Create sample orders for the last 30 days
    orders_created = 0
    for i in range(30):  # Last 30 days
        order_date = datetime.utcnow() - timedelta(days=i)

        # Create 1-3 orders per day
        for _ in range(random.randint(1, 3)):
            # Random user
            user = random.choice(users)

            # Create order
            order = Order(employee_id=user.id)
            db.session.add(order)
            db.session.flush()  # Get order ID

            # Add 2-5 random items to order
            order_items = []
            total_amount = Decimal('0.00')

            num_items = random.randint(2, 5)
            selected_products = random.sample(products, num_items)

            for product in selected_products:
                quantity = random.randint(1, 5)
                unit_price = product.price
                line_total = unit_price * quantity

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name_snapshot=product.name,
                    unit_price_snapshot=unit_price,
                    quantity=quantity,
                    line_total=line_total
                )
                db.session.add(order_item)
                total_amount += line_total

            # Update order total
            order.total_amount = total_amount
            order.created_at = order_date

            orders_created += 1

    db.session.commit()
    print(f"Added {orders_created} sample orders")

    print("Sample data added successfully!")
    print("You can now view the dashboard with real data.")