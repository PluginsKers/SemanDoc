from typing import Optional

from src import app_manager
from src.modules.database import User
from src.utils.security import check_password, generate_jwt_token


def authenticate(username: str, password: str) -> Optional[str]:
    user_db = User(app_manager.get_database_instance())
    udata = user_db.get_user(username)
    if udata is None:
        return None

    if udata and check_password(udata['password'], password):
        return generate_jwt_token(username)
    return None


def create_user(username: str, password: str, nickname: str = "Test User"):
    # Pass the database instance
    user_db = User(app_manager.get_database_instance())
    result, msg = user_db.add_user(username, password, nickname)
    return result, msg
