// Cart-specific JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    initCartQuantityUpdates();
    initCartValidation();
});

// Initialize cart quantity updates
function initCartQuantityUpdates() {
    const quantityInputs = document.querySelectorAll('.cart-quantity-input');

    quantityInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            updateLineTotal(input);
            updateCartSummary();
        });

        input.addEventListener('input', debounce(function() {
            validateQuantity(input);
        }, 300));
    });
}

// Update line total when quantity changes
function updateLineTotal(input) {
    const row = input.closest('tr') || input.closest('.cart-item');
    if (!row) return;

    const priceElement = row.querySelector('.item-price');
    const totalElement = row.querySelector('.line-total');

    if (priceElement && totalElement) {
        const price = parseFloat(priceElement.textContent.replace('$', ''));
        const quantity = parseInt(input.value) || 0;
        const total = price * quantity;

        totalElement.textContent = `$${total.toFixed(2)}`;
    }
}

// Update cart summary
function updateCartSummary() {
    const lineTotals = document.querySelectorAll('.line-total');
    let subtotal = 0;

    lineTotals.forEach(function(total) {
        subtotal += parseFloat(total.textContent.replace('$', ''));
    });

    const taxRate = 0.085; // Should match config
    const tax = subtotal * taxRate;
    const total = subtotal + tax;

    // Update summary elements
    updateSummaryElement('.cart-subtotal', subtotal);
    updateSummaryElement('.cart-tax', tax);
    updateSummaryElement('.cart-total', total);
}

function updateSummaryElement(selector, amount) {
    const element = document.querySelector(selector);
    if (element) {
        element.textContent = `$${amount.toFixed(2)}`;
    }
}

// Validate quantity input
function validateQuantity(input) {
    const max = parseInt(input.getAttribute('max')) || 999;
    const min = parseInt(input.getAttribute('min')) || 0;
    let value = parseInt(input.value) || 0;

    if (value > max) {
        value = max;
        input.value = value;
        showAlert(`Maximum quantity is ${max}`, 'warning');
    } else if (value < min) {
        value = min;
        input.value = min;
    }

    // Check stock availability
    checkStockAvailability(input, value);
}

// Check stock availability via AJAX
function checkStockAvailability(input, quantity) {
    const productId = input.getAttribute('data-product-id');
    if (!productId) return;

    fetch(`/api/product/${productId}/stock?quantity=${quantity}`)
        .then(response => response.json())
        .then(data => {
            const feedback = input.parentNode.querySelector('.invalid-feedback');
            if (!data.available) {
                input.classList.add('is-invalid');
                if (feedback) {
                    feedback.textContent = `Only ${data.available_stock} items available`;
                    feedback.style.display = 'block';
                }
                input.value = data.available_stock;
                updateLineTotal(input);
            } else {
                input.classList.remove('is-invalid');
                if (feedback) {
                    feedback.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Stock check failed:', error);
        });
}

// Initialize cart validation
function initCartValidation() {
    const checkoutForm = document.querySelector('#checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            if (!validateCartBeforeCheckout()) {
                e.preventDefault();
                return false;
            }
        });
    }
}

// Validate cart before checkout
function validateCartBeforeCheckout() {
    const cartItems = document.querySelectorAll('.cart-item');
    let isValid = true;
    let errors = [];

    cartItems.forEach(function(item) {
        const quantityInput = item.querySelector('.cart-quantity-input');
        const productName = item.querySelector('.item-name').textContent;
        const quantity = parseInt(quantityInput.value) || 0;
        const maxStock = parseInt(quantityInput.getAttribute('max')) || 0;

        if (quantity > maxStock) {
            errors.push(`${productName}: Only ${maxStock} items available`);
            isValid = false;
        } else if (quantity <= 0) {
            errors.push(`${productName}: Invalid quantity`);
            isValid = false;
        }
    });

    if (!isValid) {
        errors.forEach(function(error) {
            showAlert(error, 'danger');
        });
    }

    return isValid;
}

// Add item to cart (AJAX)
function addToCart(productId, quantity = 1) {
    const button = event.target;
    const originalText = button.innerHTML;

    setLoading(button, true);

    fetch(`/employee/cart/add/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}&csrf_token=${getCsrfToken()}`
    })
    .then(response => response.text())
    .then(html => {
        // Check if redirect occurred (success)
        if (window.location.href.includes('/employee/products')) {
            window.location.reload();
        } else {
            // Parse response for flash messages
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const alerts = doc.querySelectorAll('.alert');
            alerts.forEach(function(alert) {
                const message = alert.textContent.trim();
                const type = alert.classList.contains('alert-success') ? 'success' :
                           alert.classList.contains('alert-danger') ? 'danger' : 'info';
                showAlert(message, type);
            });
        }
    })
    .catch(error => {
        console.error('Add to cart failed:', error);
        showAlert('Failed to add item to cart', 'danger');
    })
    .finally(() => {
        setLoading(button, false);
    });
}

// Remove item from cart (AJAX)
function removeFromCart(productId) {
    if (!confirm('Remove this item from cart?')) return;

    fetch(`/employee/cart/remove/${productId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `csrf_token=${getCsrfToken()}`
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        } else {
            showAlert('Failed to remove item', 'danger');
        }
    })
    .catch(error => {
        console.error('Remove from cart failed:', error);
        showAlert('Failed to remove item', 'danger');
    });
}

// Clear cart (AJAX)
function clearCart() {
    if (!confirm('Clear entire cart?')) return;

    fetch('/employee/cart/clear', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `csrf_token=${getCsrfToken()}`
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        } else {
            showAlert('Failed to clear cart', 'danger');
        }
    })
    .catch(error => {
        console.error('Clear cart failed:', error);
        showAlert('Failed to clear cart', 'danger');
    });
}

// Get CSRF token
function getCsrfToken() {
    const tokenInput = document.querySelector('input[name="csrf_token"]');
    return tokenInput ? tokenInput.value : '';
}

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Show alert helper
function showAlert(message, type = 'info') {
    if (window.GroceryApp && window.GroceryApp.showAlert) {
        window.GroceryApp.showAlert(message, type);
    } else {
        alert(message);
    }
}

// Set loading state helper
function setLoading(button, loading = true) {
    if (window.GroceryApp && window.GroceryApp.setLoading) {
        window.GroceryApp.setLoading(button, loading);
    } else {
        button.disabled = loading;
    }
}