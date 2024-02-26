from src.utils.security import encrypt_password
from src import get_db


class User:
    def __init__(self):
        self.db = get_db()

    def user_exists(self, username: str):
        query = "SELECT * FROM users WHERE username = ?;"
        result = self.db.execute_read_query(query, (username,))
        return len(result) > 0

    def add_user(self, username: str, password: str, nickname: str):
        if self.user_exists(username):
            return False, "User already exists"

        encrypted_password = encrypt_password(password)
        query = """INSERT INTO users(username, password, nickname)
                   VALUES (?, ?, ?);"""
        self.db.execute_query(query, (username, encrypted_password, nickname))
        return True, "User added successfully"

    def get_user(self, username: str) -> tuple:
        query = "SELECT * FROM users WHERE username = ?;"
        result = self.db.execute_read_query(query, (username,))
        if len(result) != 1:
            return None
        return result[0]

    def delete_user(self, username: str):
        query = "DELETE FROM users WHERE username = ?;"
        return self.db.execute_query(query, (username,))
