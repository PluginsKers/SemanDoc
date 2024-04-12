import logging
from typing import Optional, Tuple

from src import app_manager
from src.modules.database import User, Role
from src.utils.security import check_password, generate_jwt_token

logger = logging.getLogger(__name__)

user_db = User(app_manager.get_database_instance())
role_db = Role(app_manager.get_database_instance())


def authenticate(username: str, password: str) -> Optional[str]:
    user_data = user_db.get_user(username)
    if user_data and check_password(user_data['password'], password):
        return generate_jwt_token(user_data['id'])
    return None


def get_user_by_id(id: int, **kwargs) -> Tuple[bool, Optional[dict]]:
    user_data = user_db.get_user_by_id(id)
    if user_data:
        return True, user_data
    return False, None


def create_user(username: str, password: str, role: int, nickname: str = "User", **kwargs) -> bool:
    """
    Creates a new user with the specified role and additional attributes.

    Args:
        username (str): The username of the new user.
        password (str): The password for the new user.
        role (int): The role ID associated with the user.
        nickname (str): Optional nickname for the user. Defaults to 'User'.
        **kwargs: Additional keyword arguments, expects 'user_id' to perform operation.

    Returns:
        bool: True if the user was successfully created, False otherwise.

    Raises:
        ValueError: If required user_id is missing, the role is invalid, or permissions are insufficient.
    """
    user_id = kwargs.get('user_id')
    if user_id is None:
        raise ValueError("User ID is required for creating a user.")

    try:
        user_info = user_db.get_user_by_id(int(user_id))
        if user_info is None:
            raise ValueError("User ID does not exist.")
        permissions = role_db.get_role(user_info['role_id'])
        if permissions is None or 'USERS_CONTROL' not in permissions:
            raise ValueError(
                "Invalid role or insufficient permissions to create a user.")
    except Exception as e:
        raise ValueError(f"An error occurred while verifying permissions: {e}")

    if role_db.has_role(role):
        success, message = user_db.add_user(username, password, nickname, role)
        if not success:
            logger.error(f"Failed to add user: {message}")
        return success
    else:
        raise ValueError("Specified role does not exist.")


def delete_user_by_id(id: int, **kwargs) -> bool:
    if 'user_id' in kwargs and id == int(kwargs.get('user_id', 0)):
        return False

    try:
        user_info = user_db.get_user_by_id(int(kwargs.get('user_id')))
        permissions = role_db.get_role(user_info['role_id'])
        if permissions is None:
            raise ValueError("Invalid role.")
        if permissions is None or 'USERS_CONTROL' not in permissions:
            raise ValueError(
                "Invalid role or insufficient permissions to delete a user.")
    except Exception as e:
        raise ValueError(f"An error occurred while verifying permissions: {e}")

    if user_db.delete_user_by_id(id):
        return True
    logger.error("Failed to delete user.")
    return False
