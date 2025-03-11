from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from werkzeug.utils import secure_filename
from pymongo import MongoClient, ASCENDING, GEOSPHERE
from dotenv import load_dotenv
import os
from datetime import datetime
from .routes.main import bp as main
from .routes.auth import bp as auth
from .routes.posts import bp as posts
from .routes.mod import bp as mod
from .routes.notifications import bp as notifications
from .routes.profile import bp as profile
from .routes.admin import bp as admin

# Load environment variables
load_dotenv()

# Initialize Flask extensions
login_manager = LoginManager()
mail = Mail()

# Define allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db(db):
    """Initialize database collections and indexes"""
    try:
        print("Initializing database collections...")
        
        # List of collections to create
        collections = [
            'users',
            'posts',
            'comments',
            'notifications',
            'suggestions'
        ]
        
        # Get existing collections
        existing_collections = db.list_collection_names()
        print(f"Existing collections: {existing_collections}")
        
        # Create collections if they don't exist
        for collection in collections:
            if collection not in existing_collections:
                print(f"Creating collection: {collection}")
                db.create_collection(collection)
        
        # Create indexes
        print("Creating indexes...")
        
        # Users indexes
        db.users.create_index([('email', ASCENDING)], unique=True)
        db.users.create_index([('username', ASCENDING)], unique=True)
        
        # Posts indexes
        db.posts.create_index([('author_id', ASCENDING)])
        db.posts.create_index([('location', GEOSPHERE)])
        
        # Comments indexes
        db.comments.create_index([('post_id', ASCENDING)])
        db.comments.create_index([('author_id', ASCENDING)])
        
        # Notifications indexes
        db.notifications.create_index([('user_id', ASCENDING)])
        
        print("Database initialization completed successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['MONGODB_URI'] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/suluhisho')
    
    # Mail configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
    
    if not all([
        app.config['MAIL_SERVER'],
        app.config['MAIL_PORT'],
        app.config['MAIL_USERNAME'],
        app.config['MAIL_PASSWORD']
    ]):
        print("\n=== Email Configuration Warning ===")
        print("Email settings are not fully configured:")
        print(f"MAIL_SERVER: {'Set' if app.config['MAIL_SERVER'] else 'Missing'}")
        print(f"MAIL_PORT: {'Set' if app.config['MAIL_PORT'] else 'Missing'}")
        print(f"MAIL_USERNAME: {'Set' if app.config['MAIL_USERNAME'] else 'Missing'}")
        print(f"MAIL_PASSWORD: {'Set' if app.config['MAIL_PASSWORD'] else 'Missing'}")
        print("Email functionality will not work!")
        print("===============================\n")
    
    # Upload configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    mail.init_app(app)
    app.mail = mail  # Store mail instance as app attribute
    
    # Initialize MongoDB
    try:
        print(f"Connecting to MongoDB at: {app.config['MONGODB_URI']}")
        client = MongoClient(app.config['MONGODB_URI'])
        db = client.get_default_database()
        
        # Test connection
        db.command('ismaster')
        print("MongoDB connection successful")
        
        # Initialize database collections and indexes
        if not init_db(db):
            raise Exception("Database initialization failed")
            
        app.db = db
        
        # Create geospatial index for post locations
        db.posts.create_index([("location", "2dsphere")])
        print("Created geospatial index for post locations")
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        raise

    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        from bson import ObjectId
        try:
            print(f"Loading user with ID: {user_id}")
            user_data = app.db.users.find_one({'_id': ObjectId(user_id)})
            print(f"User data found: {user_data is not None}")
            return User.from_dict(user_data) if user_data else None
        except Exception as e:
            print(f"Error loading user: {str(e)}")
            return None
    
    # Context processor for templates
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.utcnow()
        }
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(posts)
    app.register_blueprint(mod)
    app.register_blueprint(notifications)
    app.register_blueprint(profile)
    app.register_blueprint(admin)
    
    # Register template filters
    @app.template_filter('datetime')
    def format_datetime(value):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        return value.strftime('%Y-%m-%d %H:%M:%S')
    
    @app.template_filter('timeago')
    def timeago(value):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        
        now = datetime.utcnow()
        diff = now - value
        
        if diff.days > 365:
            return f"{diff.days // 365} years ago"
        elif diff.days > 30:
            return f"{diff.days // 30} months ago"
        elif diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hours ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minutes ago"
        else:
            return "just now"
    
    return app