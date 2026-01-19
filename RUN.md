# Quick Start Guide - Grocery Store Management System

## 🚀 Recommended: Run with Docker (Easiest)

### Prerequisites
- Docker & Docker Compose
- Git

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd grocery_v2
```

### 2. Start with Docker
```bash
# Build and run all services (Flask app + PostgreSQL)
docker-compose up --build
```

### 3. Access the Application
- **URL**: `http://localhost:8000`
- **Admin Login**: `admin` / `admin123`
- **Database**: PostgreSQL runs automatically in Docker

### 4. Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (removes database data)
docker-compose down -v
```

## 🔧 Manual Development Setup (Alternative)

### Prerequisites
- Python 3.11+
- PostgreSQL (local installation)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
# Copy environment template
cp .env.example .env

# Edit database connection in .env
# DATABASE_URL=postgresql://user:pass@localhost:5432/grocery_db
```

### 3. Setup Database
```bash
# Initialize database migrations
flask db init
flask db migrate
flask db upgrade

# Create admin user
flask create-admin
```

### 4. Run the Application
```bash
# Development mode
python run.py

# Or using Flask CLI
flask run --host 0.0.0.0 --port 5000
```

## 📁 Project Structure
```
grocery_v2/
├── app/                 # Flask application
│   ├── auth/           # Authentication blueprint
│   ├── admin/          # Admin dashboard & CRUD
│   ├── employee/       # Employee portal & cart
│   ├── orders/         # Invoice generation
│   ├── models.py       # SQLAlchemy models
│   └── templates/      # Jinja2 templates
├── migrations/         # Database migrations
├── static/            # CSS, JS assets
├── docker-compose.yml # Docker orchestration
├── Dockerfile         # Container definition
├── requirements.txt   # Python dependencies
├── run.py            # Development runner
└── wsgi.py           # Production WSGI
```

## 🐳 Docker Commands Reference

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Run database migrations inside container
docker-compose exec web flask db upgrade

# Create admin user inside container
docker-compose exec web flask create-admin

# Access database directly
docker-compose exec db psql -U grocery_user -d grocery_db

# Rebuild after code changes
docker-compose up --build --force-recreate

# Clean up everything
docker-compose down -v --rmi all
```

## 🔧 Troubleshooting

### Docker Issues
```bash
# If port 8000 is already in use
docker-compose down
# Then change port in docker-compose.yml

# If database connection fails
docker-compose logs db
docker-compose restart db

# Clear all Docker data
docker system prune -a --volumes
```

### Database Issues
```bash
# Reset database in Docker
docker-compose exec web flask db downgrade base
docker-compose exec web flask db upgrade
docker-compose exec web flask create-admin
```

### Import Errors
- Ensure you're in the correct directory
- Check Python path: `python -c "import sys; print(sys.path)"`
- Verify all requirements are installed

## 🎯 Features Included

- ✅ **User Authentication** (Admin/Employee roles)
- ✅ **Product Management** (CRUD with image uploads)
- ✅ **Shopping Cart** (Session-based)
- ✅ **Order Processing** (Checkout & invoices)
- ✅ **Admin Dashboard** (Metrics & reports)
- ✅ **Employee Portal** (Product browsing)
- ✅ **PostgreSQL Database** (Docker container)
- ✅ **Cloudinary Integration** (Image storage)
- ✅ **Responsive UI** (Bootstrap 5)

## 📞 Support
- Check `README.md` for detailed documentation
- View logs: `docker-compose logs -f`
- Debug: `docker-compose exec web bash`