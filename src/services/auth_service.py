import logging
from typing import Optional

from src import app_manager
from src.modules.database import User
from src.utils.security import check_password, generate_jwt_token

logger = logging.getLogger(__name__)

user_db = User(app_manager.get_database_instance())


def authenticate(username: str, password: str) -> Optional[str]:
    user_data = user_db.get_user(username)
    if user_data and check_password(user_data['password'], password):
        return generate_jwt_token(user_data['id'], user_data['password'])
    return None
