# Grocery Store Management System V2

A production-ready Flask-based Grocery Store Management System with role-based access control, inventory management, session-based cart, and invoice generation.

## 🏗️ Architecture Overview

This application follows a **Blueprint-based architecture** with the following components:

- **Backend**: Flask + SQLAlchemy + PostgreSQL + Cloudinary
- **Frontend**: Jinja templates + Bootstrap + Vanilla JavaScript
- **Security**: Flask-Login, Flask-WTF, CSRF protection, role-based access
- **Features**: Product management, cart/checkout, order management, invoicing

### Key Technologies

- **Flask** - Web framework with Blueprint architecture
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Primary database
- **Cloudinary** - Image storage and management
- **Flask-Migrate** - Database migrations
- **Flask-Login** - User authentication
- **Flask-WTF** - Forms and CSRF protection
- **Gunicorn** - WSGI server for production

## 📁 Project Structure

```
grocery_v2/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration settings
│   ├── extensions.py        # Flask extensions
│   ├── models.py            # SQLAlchemy models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py    # Role-based access decorators
│   │   ├── cloudinary_upload.py  # Image upload utilities
│   │   ├── helpers.py       # Cart and utility functions
│   │   └── cli.py           # CLI commands
│   ├── auth/                # Authentication blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── admin/               # Admin blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── employee/            # Employee blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── orders/              # Orders blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── templates/           # Jinja templates
│   │   ├── base.html
│   │   ├── partials/
│   │   │   ├── _flash.html
│   │   │   └── _navbar.html
│   │   ├── auth/
│   │   │   └── login.html
│   │   ├── admin/
│   │   │   ├── base_admin.html
│   │   │   ├── dashboard.html
│   │   │   ├── products_list.html
│   │   │   ├── product_form.html
│   │   │   ├── employees_list.html
│   │   │   ├── employee_form.html
│   │   │   └── orders_list.html
│   │   ├── employee/
│   │   │   ├── base_employee.html
│   │   │   ├── dashboard.html
│   │   │   ├── products_list.html
│   │   │   ├── cart.html
│   │   │   ├── checkout.html
│   │   │   └── orders_list.html
│   │   └── orders/
│   │       └── invoice.html
│   └── static/              # Static assets
│       ├── css/
│       │   └── styles.css
│       └── js/
│           ├── main.js
│           ├── cart.js
│           └── invoice.js
├── migrations/              # Database migrations
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── wsgi.py                  # WSGI entry point
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (or Docker)
- Cloudinary account (for image uploads)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd grocery_v2

#python -m venv venv
source venv/bin/activate  Create virtual environment
 # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Required environment variables:

```bash
# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/grocery_db

# Cloudinary (for image uploads)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Admin user
ADMIN_USER=admin
ADMIN_PASS=admin123
```

### 3. Database Setup

```bash
# Initialize database
flask db init
flask db migrate
flask db upgrade

# Create admin user
flask create-admin
```

### 4. Run the Application

```bash
# Development
flask run

# Or with Gunicorn
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

Visit `http://localhost:5000` and log in with:
- **Username**: admin
- **Password**: admin123

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

The application will be available at `http://localhost:8000`

### Manual Docker Build

```bash
# Build image
docker build -t grocery-store-v2 .

# Run container
docker run -p 8000:8000 --env-file .env grocery-store-v2
```

## 🔧 Configuration

### Database Configuration

The app supports both `DATABASE_URL` and individual database variables:

```bash
# Option 1: DATABASE_URL
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Option 2: Individual variables
DB_HOST=localhost
DB_PORT=5432
DB_NAME=grocery_db
DB_USER=postgres
DB_PASS=password
```

### Cloudinary Setup

1. Sign up at [Cloudinary](https://cloudinary.com)
2. Get your cloud name, API key, and API secret
3. Add to `.env` file
4. Images will be automatically uploaded and stored securely

### Store Configuration

Customize store information in `.env`:

```bash
STORE_NAME="Your Store Name"
STORE_ADDRESS="123 Main St, City, State 12345"
STORE_PHONE="(555) 123-4567"
STORE_EMAIL="contact@yourstore.com"
TAX_RATE=8.5
```

## 👥 User Roles & Features

### Admin User
- **Dashboard**: Overview with metrics and charts
- **Product Management**: CRUD operations with image uploads
- **Employee Management**: Create/manage employee accounts
- **Order Overview**: View all orders with filtering
- **Reports**: Sales analytics and low stock alerts

### Employee User
- **Dashboard**: Quick access and recent orders
- **Product Browsing**: Search and view products
- **Cart Management**: Add/remove items, quantity updates
- **Checkout**: Process orders with payment options
- **Order History**: View personal order history
- **Invoice Generation**: Print/download order receipts

## 🔒 Security Features

- **Password Hashing**: Werkzeug security for passwords
- **CSRF Protection**: Flask-WTF CSRF tokens
- **Session Security**: Secure cookies and session management
- **Role-Based Access**: Decorators for admin/employee routes
- **Input Validation**: Server-side form validation
- **SQL Injection Prevention**: Parameterized ORM queries

## 📊 Database Schema

### Users Table
- id, username, password_hash, role, created_at

### Products Table
- id, name, price, stock_qty, category, image_url, timestamps

### Orders Table
- id, employee_id, total_amount, tax_amount, payment_method, timestamps

### Order Items Table
- id, order_id, product_id, product_snapshot, unit_price, quantity, line_total

## 🛠️ CLI Commands

```bash
# Create admin user
flask create-admin --username admin --password securepass

# Database operations
flask db init      # Initialize migrations
flask db migrate   # Create migration
flask db upgrade   # Apply migrations
flask db downgrade # Rollback migration

# Run development server
flask run --host 0.0.0.0 --port 5000
```

## 🔄 API Endpoints

### Authentication
- `GET/POST /login` - User login
- `POST /logout` - User logout

### Admin Endpoints
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/products` - Product list
- `GET/POST /admin/products/new` - Add product
- `GET/POST /admin/products/<id>/edit` - Edit product
- `POST /admin/products/<id>/delete` - Delete product
- `GET /admin/api/sales` - Sales data API

### Employee Endpoints
- `GET /employee/dashboard` - Employee dashboard
- `GET /employee/products` - Browse products
- `POST /employee/cart/add/<id>` - Add to cart
- `GET/POST /employee/cart` - View cart
- `POST /employee/cart/clear` - Clear cart
- `GET/POST /employee/checkout` - Checkout process

### Orders
- `GET /orders/<id>/invoice` - View invoice

## 🧪 Testing

```bash
# Run tests (if implemented)
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## 🚀 Production Deployment

### Environment Setup

1. Set `FLASK_ENV=production` in `.env`
2. Use strong `SECRET_KEY`
3. Configure production database
4. Set up Cloudinary for image storage
5. Enable HTTPS (recommended)

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn --bind 0.0.0.0:8000 --workers 4 --threads 2 wsgi:app
```

### Nginx Configuration (Optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 1y;
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Database Connection Error**
- Verify DATABASE_URL format
- Ensure PostgreSQL is running
- Check database credentials

**Image Upload Fails**
- Verify Cloudinary credentials
- Check file size limits
- Ensure supported image formats

**Permission Denied**
- Check user roles and decorators
- Verify login status
- Clear browser cache/cookies

**Migration Errors**
- Backup database before migrations
- Check migration files
- Use `flask db stamp head` if needed

### Debug Mode

Enable debug logging:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run
```

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review Flask/SQLAlchemy documentation

---

**Happy coding! 🛒**