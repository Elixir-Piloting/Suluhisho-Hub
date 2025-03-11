from flask import current_app
from itsdangerous import URLSafeTimedSerializer

def get_token_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def generate_verification_token(email):
    serializer = get_token_serializer()
    return serializer.dumps(email, salt='email-verification-salt')

def verify_token(token, expiration=3600):
    serializer = get_token_serializer()
    try:
        email = serializer.loads(
            token,
            salt='email-verification-salt',
            max_age=expiration
        )
        return email
    except:
        return None 