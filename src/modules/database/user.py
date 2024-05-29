from typing import List, Optional, Set, Tuple, Union
from src.modules.database.sqlite import DatabaseManager
from src.utils.security import encrypt_password
import logging

logger = logging.getLogger(__name__)


class Role(DatabaseManager):
    def __init__(self, db: DatabaseManager):
        """
        Initialize the Role class with a database connection.

        Args:
        - db: A Database instance.
        """
        super().__init__(db.db_path)

    def create_role(self, role_name: str, permissions: Union[List[str], Set[str]]) -> Tuple[bool, str]:
        """
        Creates a new role with the given name and permissions.
        Args:
            role_name: The name of the role.
            permissions: The permissions assigned to the role, either as a list or a set.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure, and a message.
        """
        try:
            # Convert permissions to a comma-separated string
            permissions_str = ",".join(permissions)
            sql = "INSERT INTO roles (role_name, permissions) VALUES (?, ?)"
            self.execute_query(sql, (role_name, permissions_str))
            return True, "Role created successfully."
        except Exception as e:
            logger.error(f"Failed to create role {role_name}: {e}")
            return False, f"Error: {e}"

    def get_role(self, role_id: int) -> Optional[Set[str]]:
        """
        Retrieves the permissions of a role by its ID.
        Args:
            role_id: The ID of the role.

        Returns:
            Optional[Set[str]]: An Optional containing a set of permissions if the role exists, None otherwise.
        """
        if not isinstance(role_id, int):
            logger.error(
                "Role ID must be an integer.")
            return None

        try:
            sql = "SELECT permissions FROM roles WHERE id = ?"
            result = self.execute_read_query(sql, (role_id,), fetchone=True)
            if result:
                permissions = result[0].split(",") if result[0] else set()
                return set(permissions)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve role {role_id}: {e}")
            return None

    def check_permission(self, role_id: int, permission: str) -> bool:
        """
        Checks if the specified role has the given permission.

        Args:
            role_id: The ID of the role to check.
            permission: The permission to check for.

        Returns:
            bool: True if the role has the permission, False otherwise.
        """
        permissions = self.get_role(role_id)
        if permissions is None:
            return False
        return permission in permissions

    def has_role(self, role_id: int) -> bool:
        """
        Checks if a role exists by its ID.

        Args:
            role_id: The ID of the role to check.

        Returns:
            bool: True if the role exists, False otherwise.
        """
        if not isinstance(role_id, int):
            logger.error(
                "Role ID must be an integer.")
            return False

        try:
            sql = "SELECT id FROM roles WHERE id = ?"
            result = self.execute_read_query(sql, (role_id,), fetchone=True)
            return result is not None
        except Exception as e:
            logger.error(f"Failed to check role {role_id}: {e}")
            return False

    def delete_role(self, role_id: int) -> bool:
        """
        Deletes a role by its ID.

        Args:
            role_id: The ID of the role to delete.

        Returns:
            bool: True if the role was deleted successfully, False otherwise.
        """
        if not isinstance(role_id, int):
            logger.error(
                "Role ID must be an integer.")
            return False

        if not self.has_role(role_id):
            logger.error(f"Role {role_id} does not exist.")
            return False

        try:
            sql = "DELETE FROM roles WHERE id = ?"
            self.execute_query(sql, (role_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete role {role_id}: {e}")
            return False


class User(DatabaseManager):
    def __init__(self, db: DatabaseManager):
        """
        Initialize the User class with a database connection.

        Args:
            db: A Database instance.
        """
        super().__init__(db.db_path)

    def user_exists(self, username: str) -> bool:
        """
        Checks if a user exists by username.

        Args:
            username: The username to check.

        Returns:
            bool: True if the user exists, False otherwise.
        """
        query = "SELECT 1 FROM users WHERE username = ?;"
        result = self.execute_read_query(query, (username,))
        if result is None:
            logger.error(
                "Failed to execute query or connection error occurred.")
            return False
        return len(result) > 0

    def user_exists_by_id(self, user_id: int) -> bool:
        """
        Checks if a user exists by ID.

        Args:
            user_id: The ID of the user to check.

        Returns:
            bool: True if the user exists, False otherwise.
        """
        query = "SELECT 1 FROM users WHERE id = ?"
        result = self.execute_read_query(query, (user_id,))
        if result is None:
            logger.error(
                "Failed to execute query or connection error occurred.")
            return False
        return len(result) > 0

    def add_user(self, username: str, password: str, nickname: str, role_id: int) -> Tuple[bool, str]:
        """
        Adds a new user to the database with encrypted password.

        Args:
            username: The username of the new user.
            password: The password of the new user.
            role_id: The role_id of the new user.
            nickname: The nickname of the new user.

        Returns
            Tuple[bool, str]: A tuple of (bool, str) indicating success and a message.
        """
        if self.user_exists(username):
            return False, "User already exists."

        encrypted_password = encrypt_password(password)
        query = """INSERT INTO users(username, password, nickname, role_id)
                   VALUES (?, ?, ?, ?);"""
        try:
            self.execute_query(
                query, (username, encrypted_password, nickname, role_id))
            return True, "User added successfully."
        except Exception as e:
            logger.error(f"Failed to add user: {e}")
            return False, "Failed to add user."

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """
        Retrieves user information by username, excluding the password.

        Args:
            username: The username of the user to retrieve.

        Returns:
            Optional[dict]: A dictionary of the user information or None if not found.
        """
        query = "SELECT id, username, password, nickname, role_id FROM users WHERE username = ?;"
        result = self.execute_read_query(query, (username,))
        if result and len(result) == 1:
            keys = ['id', 'username', 'password', 'nickname', 'role_id']
            return dict(zip(keys, result[0]))
        return None

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """
        Retrieves user information by user ID, excluding the password.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            Optional[dict]: A dictionary of the user information or None if not found.
        """
        query = "SELECT id, username, nickname, role_id FROM users WHERE id = ?;"
        result = self.execute_read_query(query, (user_id,))
        if result and len(result) == 1:
            # Mapping database columns to dictionary keys
            keys = ['id', 'username', 'nickname', 'role_id']
            return dict(zip(keys, result[0]))
        return None

    def get_users_excluding_roles(self, role_ids: Optional[List[int]] = None) -> List[dict]:
        """
        Retrieves all users whose role ID is not in the specified list of role IDs.
        If no role IDs are provided, all users will be returned.

        Args:
            role_ids: Optional list of role IDs to exclude from the results. If None or empty, all users are returned.

        Returns:
            List[dict]: A list of dictionaries, each representing a user whose role ID is not in the provided list,
                        or all users if no role IDs are provided.
        """
        if role_ids and len(role_ids) > 0:
            # Create placeholders for SQL query
            placeholders = ','.join('?' for _ in role_ids)
            query = f"SELECT id, username, nickname, role_id FROM users WHERE role_id NOT IN ({placeholders});"
            result = self.execute_read_query(query, tuple(role_ids))
        else:
            query = "SELECT id, username, nickname, role_id FROM users;"
            result = self.execute_read_query(query)

        if result:
            keys = ['id', 'username', 'nickname', 'role_id']
            return [dict(zip(keys, row)) for row in result]
        return []

    def get_users_by_role_id(self, role_id: int) -> List[dict]:
        """
        Retrieves all users with the given role ID.

        Args:
            role_id: The ID of the role.

        Returns:
            List[dict]: A list of dictionaries, each representing a user with the given role ID.
        """
        query = "SELECT id, username, nickname, role_id FROM users WHERE role_id = ?;"
        result = self.execute_read_query(query, (role_id,))
        if result:
            keys = ['id', 'username', 'nickname', 'role_id']
            return [dict(zip(keys, row)) for row in result]
        return []

    def delete_user_by_id(self, user_id: int) -> bool:
        """
        Deletes a user by their ID.

        Args:
            user_id (int): The ID of user.

        Returns:
            bool: True if the user was deleted successfully, False otherwise.
        """
        if not self.user_exists_by_id(user_id):
            return False

        query = "DELETE FROM users WHERE id = ?;"
        try:
            self.execute_query(query, (user_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False

    def update_user_nickname(self, user_id: int, nickname: str) -> bool:
        """
        Updates the nickname of a user by their ID.

        Args:
            user_id (int): The ID of user.
            nickname (str): The new nickname.

        Returns:
            bool: True if the nickname was updated successfully, False otherwise.
        """

        # TODO: block test.

        if not self.user_exists_by_id(user_id):
            return False

        query = "UPDATE users SET nickname = ? WHERE id = ?;"
        try:
            self.execute_query(query, (nickname, user_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update user nickname: {e}")
            return False

    def update_user_password(self, user_id: int, password: str) -> bool:
        if not self.user_exists_by_id(user_id):
            return False
        encrypted_password = encrypt_password(password)
        query = "UPDATE users SET password = ? WHERE id = ?;"
        try:
            self.execute_query(query, (encrypted_password, user_id))
            return True
        except Exception as e:
            logger.error(f"Failed to update user password: {e}")
            return False

    def update_user(self, user_id: int, password: Optional[str] = None, nickname: Optional[str] = None, role_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Updates user information.

        Args:
            user_id: The ID of the user to update.
            username: The new username (optional).
            password: The new password (optional, will be encrypted).
            nickname: The new nickname (optional).
            role_id: The new role ID (optional).

        Returns:
            Tuple[bool, str]: A tuple of (bool, str) indicating success and a message.
        """
        if not self.user_exists_by_id(user_id):
            return False, "User does not exist."

        fields = []
        values = []

        if password:
            encrypted_password = encrypt_password(password)
            fields.append("password = ?")
            values.append(encrypted_password)
        if nickname:
            fields.append("nickname = ?")
            values.append(nickname)
        if role_id is not None:
            fields.append("role_id = ?")
            values.append(role_id)

        if not fields:
            return False, "No fields to update."

        query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?;"
        values.append(user_id)

        try:
            self.execute_query(query, tuple(values))
            return True, "User updated successfully."
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return False, "Failed to update user."
