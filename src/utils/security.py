from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "YOUR_SECRET_KEY"


def encrypt_password(password: str):
    return generate_password_hash(password)


def check_password(hash: str, password: str):
    return check_password_hash(hash, password)


def generate_jwt_token(username: str):
    payload = {
        "exp": datetime.utcnow() + timedelta(days=1),  # Token expires in 1 day
        "iat": datetime.utcnow(),
        "sub": username,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
