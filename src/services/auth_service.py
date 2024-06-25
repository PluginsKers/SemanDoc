import functools
import logging
from typing import List, Optional, Tuple

from src import app_manager
from src.modules.database import User, Role
from src.utils.security import check_password, generate_jwt_token

logger = logging.getLogger(__name__)

userDB = User(app_manager.get_database_instance())
roleDB = Role(app_manager.get_database_instance())


def check_permissions(required_permissions: List[str]):
    """
    Decorator function to check if a user has the required permissions to perform a specific action.

    Args:
        required_permissions (List[str]): List of permissions that need to be checked.
    """
    def decorator_check_permissions(func):
        @functools.wraps(func)
        def wrapper_check_permissions(*args, **kwargs):
            user_id = kwargs.get('user_id')
            if user_id is None:
                raise ValueError("User ID is required.")

            user_info = userDB.get_user_by_id(user_id)
            if user_info is None:
                raise ValueError("User does not exist.")

            user_role_id = user_info['role_id']
            for permission in required_permissions:
                if not roleDB.check_permission(user_role_id, permission):
                    raise ValueError(
                        f"User does not have permission: {permission}")

            return func(*args, **kwargs)
        return wrapper_check_permissions
    return decorator_check_permissions


def authenticate(username: str, password: str) -> Tuple[Optional[str], Optional[dict]]:
    user_data = userDB.get_user_by_username(username)
    if user_data and check_password(user_data['password'], password):
        return generate_jwt_token(user_data['id'], user_data['password']), user_data
    return None, None
