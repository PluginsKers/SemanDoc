import sqlite3
from sqlite3 import Error
import logging
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db: str):
        """
        Initialize the database class with the database file path.

        Args:
        - db (str): Path to the SQLite database file.
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

    def execute_query(self, query: str, args: tuple = ()) -> Optional[int]:
        """
        Execute an SQL modification query using the thread-local connection.

        Args:
        - query (str): The SQL query to execute.
        - args (tuple): The arguments to the SQL query.

        Returns:
        int or None: The last row id from the query, or None if an error occurred.
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, args)
            conn.commit()
            return cur.lastrowid
        except Error as e:
            logger.error("Failed to execute query: %s", e)
            return None

    def execute_read_query(self, query: str, args: tuple = ()) -> Optional[list]:
        """
        Execute a read SQL query using the thread-local connection.

        Args:
        - query (str): The SQL query for reading data.
        - args (tuple): The arguments to the SQL query.

        Returns:
        list or None: The query result set, or None if an error occurred.
        """
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, args)
            return cur.fetchall()
        except Error as e:
            logger.error("Failed to read from database: %s", e)
            return None

    def check_and_initialize_tables(self):
        """
        Check for necessary tables and create them if they don't exist.
        """
        user_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nickname TEXT);
        """

        document_table_sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_content TEXT NOT NULL,
            metadata TEXT NOT NULL,
            UNIQUE(page_content, metadata)
        );
        """

        self.execute_query(user_table_sql)
        self.execute_query(document_table_sql)
