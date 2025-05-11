import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db, csrf, login_manager, jwt

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")

# Initialize extensions with app
db.init_app(app)

# Add custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    import json
    return json.loads(value) if value else []
csrf.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
jwt.init_app(app)

# Create all tables
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    import models
    
    db.create_all()

# Register blueprints
from auth import auth_bp
from database import db_bp

app.register_blueprint(auth_bp)
app.register_blueprint(db_bp)

# Root route
@app.route('/')
def index():
    from flask import render_template
    return render_template('index.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    from flask import render_template
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    from flask import render_template
    return render_template('base.html', error="Internal server error"), 500

# Load user from user_id
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
