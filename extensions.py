from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect

# Initialize extensions
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()