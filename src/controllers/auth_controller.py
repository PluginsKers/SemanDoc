from src.modules.db.user import User
from src.utils.security import check_password, generate_jwt_token


def authenticate(username: str, password: str):
    user_db = User()
    user = user_db.get_user(username)
    if user and check_password(user[2], password):
        return generate_jwt_token(username)
    return None


def create_user(username: str, password: str, nickname: str = "Test User"):
    user_db = User()
    result, msg = user_db.add_user(username, password, nickname)
    return result, msg
