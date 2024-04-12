import sqlite3
from sqlite3 import Error
import logging
import threading
from typing import Any, Optional

from src.utils.security import encrypt_password

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db: str):
        """
        Initialize the database class with the database file path.

        Args:
            db (str): Path to the SQLite database file.
        """
        self.db_file = db
        self.thread_conn = threading.local()

    def get_connection(self) -> sqlite3.Connection:
        """
        Get or create a thread-local database connection.

        Returns:
            sqlite3.Connection: The SQLite database connection.
        """
        if not hasattr(self.thread_conn, "conn"):
            self.create_connection()
        return self.thread_conn.conn

    def create_connection(self):
        """
        Create and store a new SQLite database connection in thread-local storage.
        """
        try:
            self.thread_conn.conn = sqlite3.connect(
                self.db_file, check_same_thread=False)
            logger.info("Connected to SQLite database, version: %s",
                        sqlite3.version)
            self.check_and_initialize_tables()
        except Error as e:
            logger.error("Database connection failed: %s", e)
            raise

    def close_connection(self):
        """Close the thread-local database connection."""
        if hasattr(self.thread_conn, "conn"):
            self.thread_conn.conn.close()
            delattr(self.thread_conn, "conn")

    def execute_query(self, query: str, args: tuple = ()) -> int:
        """
        Execute an SQL modification query using the thread-local connection.

        Args:
            query (str): The SQL query to execute.
            args (tuple): The arguments to the SQL query.

        Returns:
            int: The last row id from the query.

        Raises:
            sqlite3.Error: If the query execution fails.
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, args)
            conn.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            logger.error("Failed to execute query: %s", e)
            raise

    def execute_read_query(self, query: str, args: tuple = (), fetchone: bool = False) -> list:
        """
        Execute a read SQL query using the thread-local connection.

        Args:
            query (str): The SQL query for reading data.
            args (tuple): The arguments to the SQL query.

        Returns:
            list: The query result set.

        Raises:
            sqlite3.Error: If the read operation fails.
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, args)
            if fetchone:
                # Wrapping in list for consistent return type
                return cur.fetchone()
            else:
                return cur.fetchall()
        except sqlite3.Error as e:
            logger.error("Failed to read from database: %s", e)
            raise

    def is_table_empty(self, table_name: str) -> bool:
        """
        Check if a given table is empty.

        Args:
            table_name (str): The name of the table to check.

        Returns:
            bool: True if the table is empty, False otherwise.
        """
        check_sql = f"SELECT COUNT(*) FROM {table_name};"
        result = self.execute_read_query(check_sql)
        if result:
            # Since result is a list of tuples, get the first element of the first tuple
            count = result[0][0]
            return count == 0
        else:
            logger.error(f"Failed to check if table {table_name} is empty.")
            return False  # Assuming failure to execute query implies table existence/contents unknown

    def _initialize_default_user(self):
        if self.is_table_empty("users"):
            default_user_sql = """
            INSERT INTO users (username, password, nickname, role_id)
            VALUES ('admin', '{}', 'Administrator', 1);
            """.format(encrypt_password('admin'))  # Assuming encrypt_password is a function you've defined
            self.execute_query(default_user_sql)
            logger.info("Default top-level user created.")

    def _initialize_default_roles(self):
        if self.is_table_empty("roles"):
            default_roles = [
                ("ADMIN", "USERS_CONTROL,DOCUMENTS_CONTROL",),
                ("USER", "DOCUMENTS_CONTROL",)
            ]
            insert_role_sql = "INSERT INTO roles (role_name, permissions) VALUES (?, ?);"
            for role in default_roles:
                self.execute_query(insert_role_sql, role)
            logger.info("Default roles created.")

    def check_and_initialize_tables(self):
        """
        Check for necessary tables and create them if they don't exist.
        """

        roles_table_sql = """
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT NOT NULL UNIQUE,
            permissions TEXT);
        """

        user_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nickname TEXT,
            role_id INTEGER NOT NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id));
        """

        document_history_table_sql = """
        CREATE TABLE IF NOT EXISTS document_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            editor_id INTEGER NOT NULL,
            edit_time DATETIME NOT NULL,
            edit_description TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id),
            FOREIGN KEY (editor_id) REFERENCES users(id));
        """

        document_table_sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_content TEXT NOT NULL,
            metadata TEXT NOT NULL,
            UNIQUE(page_content, metadata)
        );
        """

        self.execute_query(roles_table_sql)
        self.execute_query(user_table_sql)
        self.execute_query(document_table_sql)
        self.execute_query(document_history_table_sql)

        self._initialize_default_user()
        self._initialize_default_roles()
