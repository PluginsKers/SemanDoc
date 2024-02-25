from . import Database


class User:
    def __init__(self, db: Database):
        self.db = db

    def add_user(self, username, password, nickname):
        query = """INSERT INTO users(username, password, nickname)
                   VALUES (?, ?, ?)
                   ON CONFLICT(username) DO UPDATE SET
                   password = excluded.password,
                   nickname = excluded.nickname;"""
        return self.db.execute_query(query, (username, password, nickname))

    def get_user(self, username):
        query = "SELECT * FROM users WHERE username = ?;"
        return self.db.execute_read_query(query, (username,))

    def delete_user(self, username):
        query = "DELETE FROM users WHERE username = ?;"
        return self.db.execute_query(query, (username,))
