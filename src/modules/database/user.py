from typing import Optional, Tuple
from src.modules.database.sqlite import Database
from src.utils.security import encrypt_password
import logging

logger = logging.getLogger(__name__)


class User(Database):
    def __init__(self, db: Database):
        """
        Initialize the User class with a database connection.

        Args:
        - db: A Database instance.
        """
        super().__init__(db.db_file)

    def user_exists(self, username: str) -> bool:
        """
        Checks if a user exists by username.

        Args:
        - username: The username to check.

        Returns:
        Bool: True if the user exists, False otherwise.
        """
        query = "SELECT 1 FROM users WHERE username = ?;"
        result = self.execute_read_query(query, (username,))
        return len(result) > 0

    def add_user(self, username: str, password: str, nickname: str) -> Tuple[bool, str]:
        """
        Adds a new user to the database with encrypted password.

        Args:
        - username: The username of the new user.
        - password: The password of the new user.
        - nickname: The nickname of the new user.

        Returns
        Tuple[bool, str]: A tuple of (bool, str) indicating success and a message.
        """
        if self.user_exists(username):
            return False, "User already exists."

        encrypted_password = encrypt_password(password)
        query = """INSERT INTO users(username, password, nickname)
                   VALUES (?, ?, ?);"""
        try:
            self.execute_query(query, (username, encrypted_password, nickname))
            return True, "User added successfully."
        except Exception as e:
            logger.error(f"Failed to add user: {e}")
            return False, "Failed to add user."

    def get_user(self, username: str) -> Optional[dict]:
        """
        Retrieves user information by username, excluding the password.

        Args:
        - username: The username of the user to retrieve.

        Returns
        Optional[dict]: A dictionary of the user information or None if not found.
        """
        query = "SELECT id, username, nickname, password FROM users WHERE username = ?;"
        result = self.execute_read_query(query, (username,))
        if result and len(result) == 1:
            keys = ['id', 'username', 'nickname', 'password']
            return dict(zip(keys, result[0]))
        return None

    def delete_user(self, username: str) -> Tuple[bool, str]:
        """
        Deletes a user from the database by username.

        Args:
        - username: The username of the user to delete.

        Returns
        Tuple[bool, str]: A tuple of (bool, str) indicating success and a message.
        """
        if not self.user_exists(username):
            return False, "User does not exist."

        query = "DELETE FROM users WHERE username = ?;"
        try:
            self.execute_query(query, (username,))
            return True, "User deleted successfully."
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False, "Failed to delete user."
