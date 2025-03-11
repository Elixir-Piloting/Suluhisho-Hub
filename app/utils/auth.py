import bcrypt
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def check_password(password, hashed):
    """Check if a password matches its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def generate_token(email):
    """Generate a verification token for email confirmation"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')

def verify_token(token, expiration=3600):
    """Verify a token and return the email if valid"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-confirm',
            max_age=expiration
        )
        return email
    except:
        return None 