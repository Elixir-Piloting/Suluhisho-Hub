from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson import ObjectId
from flask import current_app

class User(UserMixin):
    def __init__(self, username=None, email=None, password=None, _id=None, is_admin=False, 
                 is_moderator=False, profile_picture=None, is_verified=False, created_at=None, 
                 last_seen=None, preferences=None):
        self._id = _id if _id else ObjectId()
        self.username = username
        self.email = email
        self.password_hash = password  # This will store the hashed password
        self.is_admin = is_admin
        self.is_moderator = is_moderator
        self.profile_picture = profile_picture
        self.is_verified = is_verified
        self.created_at = created_at or datetime.utcnow()
        self.last_seen = last_seen or datetime.utcnow()
        self.preferences = preferences or {
            'email_notifications': True,
            'profile_visibility': 'public'
        }

    def get_id(self):
        return str(self._id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def save(self):
        try:
            print("Attempting to save user to database...")
            print("User data:", self.to_dict())
            
            if not current_app.db:
                raise Exception("Database connection not available")
            
            result = current_app.db.users.update_one(
                {'_id': self._id},
                {'$set': self.to_dict()},
                upsert=True
            )
            
            print(f"MongoDB update result - matched: {result.matched_count}, modified: {result.modified_count}, upserted_id: {result.upserted_id}")
            return True
            
        except Exception as e:
            print(f"Error saving user to database: {str(e)}")
            raise

    def to_dict(self):
        return {
            '_id': self._id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'is_admin': self.is_admin,
            'is_moderator': self.is_moderator,
            'profile_picture': self.profile_picture,
            'is_verified': self.is_verified,
            'created_at': self.created_at,
            'last_seen': self.last_seen,
            'preferences': self.preferences
        }

    @staticmethod
    def from_dict(data):
        if not data:
            return None
        return User(
            _id=data.get('_id'),
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password_hash'),
            is_admin=data.get('is_admin', False),
            is_moderator=data.get('is_moderator', False),
            profile_picture=data.get('profile_picture'),
            is_verified=data.get('is_verified', False),
            created_at=data.get('created_at'),
            last_seen=data.get('last_seen'),
            preferences=data.get('preferences')
        )

    @staticmethod
    def get_by_email(email):
        try:
            print(f"Searching for user with email: {email}")
            data = current_app.db.users.find_one({'email': email})
            print(f"Database result for email search: {data}")
            return User.from_dict(data) if data else None
        except Exception as e:
            print(f"Error getting user by email: {str(e)}")
            return None

    @staticmethod
    def get_by_username(username):
        try:
            print(f"Searching for user with username: {username}")
            data = current_app.db.users.find_one({'username': username})
            print(f"Database result for username search: {data}")
            return User.from_dict(data) if data else None
        except Exception as e:
            print(f"Error getting user by username: {str(e)}")
            return None

    @staticmethod
    def get_by_id(user_id):
        try:
            data = current_app.db.users.find_one({'_id': ObjectId(user_id)})
            return User.from_dict(data) if data else None
        except Exception as e:
            print(f"Error getting user by id: {str(e)}")
            return None

    def get_stats(self, db):
        posts = list(db.posts.find({'author_id': str(self._id), 'is_deleted': False}))
        suggestions = list(db.suggestions.find({'author_id': str(self._id), 'is_deleted': False}))
        comments = list(db.comments.find({'author_id': str(self._id), 'is_deleted': False}))
        
        return {
            'total_posts': len(posts),
            'total_comments': len(comments),
            'total_suggestions': len(suggestions),
            'resolved_posts': sum(1 for post in posts if post.get('status') == 'resolved'),
            'total_upvotes': sum(len(post.get('upvotes', [])) for post in posts)
        } 