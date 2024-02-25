import sqlite3
from sqlite3 import Error


class Database:
    def __init__(self, db_file):
        """Initialize the database connection. If the database file does not exist, it creates one, and checks the status of tables."""
        self.db_file = db_file
        self.conn = self.create_connection(db_file)
        # Check and initialize tables
        self.check_and_initialize_tables()

    def create_connection(self, db_file):
        """Create a database connection to the SQLite database specified by db_file."""
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            print(
                "SQLite database successfully created/connected, version:", sqlite3.version)
        except Error as e:
            raise Exception(f"Failed to connect to database: {e}")
        return conn

    def get_db_connection(self):
        """Return the database connection."""
        return self.conn

    def close_connection(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def execute_query(self, query, args=()):
        """Execute an SQL query."""
        try:
            cur = self.conn.cursor()
            cur.execute(query, args)
            self.conn.commit()
            return cur.lastrowid
        except Error as e:
            print(f"SQL execution error: {e}")
            return None

    def execute_read_query(self, query, args=()):
        """Execute a query to read data."""
        try:
            cur = self.conn.cursor()
            cur.execute(query, args)
            result = cur.fetchall()
            return result
        except Error as e:
            print(f"SQL read error: {e}")
            return None

    def check_and_initialize_tables(self):
        """Check and initialize tables."""
        try:
            user_table_sql = """CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT NOT NULL UNIQUE,
                                password TEXT NOT NULL,
                                nickname TEXT NOT NULL);"""

            document_table_sql = """CREATE TABLE IF NOT EXISTS documents (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    content TEXT NOT NULL,
                                    source_info TEXT NOT NULL);"""

            self.execute_query(user_table_sql)
            self.execute_query(document_table_sql)
        except Error as e:
            raise Exception(f"Failed to initialize tables: {e}")
