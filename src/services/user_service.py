import logging
from typing import Optional, Tuple

from src import app_manager
from src.modules.database import User, Role

logger = logging.getLogger(__name__)

user_db = User(app_manager.get_database_instance())
role_db = Role(app_manager.get_database_instance())


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

        if not role_db.check_permission(user_info['role_id'], 'USERS_CONTROL'):
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


def get_users(**kwargs) -> Tuple[bool, Optional[list]]:
    """
    Retrieves users based on user permissions. Users with 'USERS_CONTROL' permission can view others excluding themselves.

    Args:
        **kwargs: Dictionary containing 'user_id' which indicates the ID of the user making the request.

    Returns:
        Tuple[bool, Optional[list]]: A tuple with a boolean indicating success, and a list of users or None.

    Raises:
        ValueError: If user_id is not provided or user does not exist.
    """
    user_id = kwargs.get('user_id')
    if user_id is None:
        raise ValueError("User ID is required for getting users.")

    try:
        user_info = user_db.get_user_by_id(int(user_id))
        if user_info is None:
            raise ValueError("User ID does not exist.")

        if role_db.check_permission(user_info['role_id'], 'USERS_CONTROL'):
            return True, user_db.get_users_excluding_roles([user_info['role_id']])
        else:
            return False, None

    except Exception as e:
        raise ValueError(f"An error occurred while verifying permissions: {e}")


def get_user_by_id(id: int, **kwargs) -> Tuple[bool, Optional[dict]]:
    """
    Retrieves a specific user by their ID, with access control based on user permissions.

    Args:
        id (int): The ID of the user to retrieve.
        **kwargs: Dictionary containing 'user_id' to identify the user making the request.

    Returns:
        Tuple[bool, Optional[dict]]: A tuple with a boolean indicating success and a dictionary of user information, or None.

    Raises:
        ValueError: If user_id is not provided, user does not exist, or permissions are insufficient.
    """
    user_id = kwargs.get('user_id')
    if user_id is None:
        raise ValueError("User ID is required for creating a user.")

    try:
        user_info = user_db.get_user_by_id(int(user_id))
        if user_info is None:
            raise ValueError("User ID does not exist.")
        if not role_db.check_permission(user_info['role_id'], 'USERS_CONTROL'):
            return True, user_info
        else:
            user_data = user_db.get_user_by_id(id)
            if user_data:
                return True, user_data
    except Exception as e:
        raise ValueError(f"An error occurred while verifying permissions: {e}")

    return False, None


def delete_user_by_id(id: int, **kwargs) -> bool:
    """
    Deletes a specific user by their ID, with access control based on user permissions.

    Args:
        id (int): The ID of the user to delete.
        **kwargs: Dictionary containing 'user_id' to identify the user making the request.

    Returns:
        bool: True if the user was deleted successfully, False otherwise.

    Raises:
        ValueError: If user_id is not provided, user does not exist, or permissions are insufficient.
    """
    if 'user_id' in kwargs and id == int(kwargs.get('user_id', 0)):
        return False

    try:
        user_info = user_db.get_user_by_id(int(kwargs.get('user_id')))
        if not role_db.check_permission(user_info['role_id'], 'USERS_CONTROL'):
            raise ValueError(
                "Invalid role or insufficient permissions to delete a user.")
    except Exception as e:
        raise ValueError(f"An error occurred while verifying permissions: {e}")

    if user_db.delete_user_by_id(id):
        return True
    logger.error("Failed to delete user.")
    return False
