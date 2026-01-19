from flask import session, flash
from decimal import Decimal, ROUND_HALF_UP
from config import Config


def get_cart():
    """Get cart from session, creating empty cart if none exists."""
    return session.get('cart', {})


def add_to_cart(product_id, quantity=1):
    """Add item to cart in session."""
    cart = get_cart()
    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity

    session['cart'] = cart
    session.modified = True


def update_cart_item(product_id, quantity):
    """Update quantity of item in cart."""
    cart = get_cart()
    product_id = str(product_id)

    if quantity <= 0:
        remove_from_cart(product_id)
        return

    if product_id in cart:
        cart[product_id] = quantity
        session['cart'] = cart
        session.modified = True


def remove_from_cart(product_id):
    """Remove item from cart."""
    cart = get_cart()
    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart
        session.modified = True


def clear_cart():
    """Clear entire cart."""
    session['cart'] = {}
    session.modified = True


def get_cart_total(cart_items):
    """Calculate total price for cart items."""
    total = Decimal('0.00')
    for item in cart_items:
        total += item['line_total']
    return total


def calculate_tax(amount):
    """Calculate tax amount."""
    tax_rate = Decimal(str(Config.TAX_RATE)) / Decimal('100')
    return (amount * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


# Currency conversion settings
USD_TO_INR_RATE = Decimal('83.50')  # Current approximate USD to INR rate

def usd_to_inr(amount):
    """Convert USD amount to INR."""
    if isinstance(amount, str):
        amount = Decimal(amount)
    return (amount * USD_TO_INR_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def format_currency_usd(amount):
    """Format amount as USD currency string."""
    if isinstance(amount, str):
        amount = Decimal(amount)
    return f"${amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"

def format_currency_inr(amount):
    """Format amount as INR currency string."""
    if isinstance(amount, str):
        amount = Decimal(amount)
    return f"₹{amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"

def format_currency(amount, currency='both'):
    """
    Format amount as currency string.
    Options: 'usd', 'inr', 'both'
    """
    if isinstance(amount, str):
        amount = Decimal(amount)

    if currency == 'usd':
        return format_currency_usd(amount)
    elif currency == 'inr':
        return format_currency_inr(usd_to_inr(amount))
    else:  # 'both'
        usd = format_currency_usd(amount)
        inr = format_currency_inr(usd_to_inr(amount))
        return f"{usd} ({inr})"


def get_cart_count():
    """Get total number of items in cart."""
    cart = get_cart()
    return sum(cart.values())


def validate_cart_stock(cart, products):
    """
    Validate that cart items have sufficient stock.

    Args:
        cart: Cart dictionary {product_id: quantity}
        products: List of Product objects

    Returns:
        dict: {'valid': bool, 'errors': list of error messages}
    """
    errors = []
    product_dict = {str(p.id): p for p in products}

    for product_id, quantity in cart.items():
        product = product_dict.get(product_id)
        if not product:
            errors.append(f"Product {product_id} not found")
        elif not product.can_fulfill_quantity(quantity):
            errors.append(f"Insufficient stock for {product.name}. Available: {product.stock_qty}")

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }