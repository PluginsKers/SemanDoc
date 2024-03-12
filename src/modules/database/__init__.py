import sqlite3
import logging
from sqlite3 import Error
import threading

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_file: str):
        """Initialize with the database file, but don't create a connection yet."""
        self.db_file = db_file
        # Use threading.local to store connection per thread
        self.thread_conn = threading.local()

    def get_connection(self):
        """Get a thread-local database connection."""
        if not hasattr(self.thread_conn, "conn"):
            self.create_connection()
        return self.thread_conn.conn

    def create_connection(self):
        """Create a database connection to the SQLite database specified by db_file, and store it in thread-local storage."""
        try:
            self.thread_conn.conn = sqlite3.connect(
                self.db_file, check_same_thread=False)
            logger.info(
                "SQLite database successfully created/connected, version: %s", sqlite3.version)
            # Ensure tables are checked/initialized for each new connection
            self.check_and_initialize_tables()
        except Error as e:
            logger.error("Failed to connect to database: %s", e)
            raise

    def close_connection(self):
        """Close the database connection for the current thread."""
        if hasattr(self.thread_conn, "conn"):
            self.thread_conn.conn.close()
            del self.thread_conn.conn  # Remove connection from thread-local storage

    def execute_query(self, query: str, args=()):
        """Execute an SQL query using the thread-local connection."""
        conn = self.get_connection()  # Get the thread-local connection
        try:
            cur = conn.cursor()
            cur.execute(query, args)
            conn.commit()
            return cur.lastrowid
        except Error as e:
            logger.error("SQL execution error: %s", e)
            return None

    def execute_read_query(self, query: str, args=()) -> list:
        """Execute a query to read data using the thread-local connection."""
        conn = self.get_connection()  # Get the thread-local connection
        try:
            cur = conn.cursor()
            cur.execute(query, args)
            result = cur.fetchall()
            return result
        except Error as e:
            logger.error("SQL read error: %s", e)
            return None

    def check_and_initialize_tables(self):
        """Check and initialize tables using the thread-local connection."""
        conn = self.get_connection()  # Ensure we're working with the correct connection
        user_table_sql = """CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE,
                            password TEXT NOT NULL,
                            nickname TEXT NOT NULL);"""

        document_table_sql = """CREATE TABLE IF NOT EXISTS documents (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                page_content TEXT NOT NULL,
                                metadata TEXT NOT NULL);"""

        self.execute_query(user_table_sql)
        self.execute_query(document_table_sql)
