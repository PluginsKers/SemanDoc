import logging
import sqlite3
from src.modules.database.sqlite import Database

logger = logging.getLogger(__name__)


class Document(Database):
    def __init__(self, db: Database):
        """
        Initialize the Document class with a database connection.

        Args:
        - db: A Database instance.
        """
        super().__init__(db.db_file)

    def add_document(self, page_content: str, metadata: str) -> bool:
        """
        Adds a new document to the database. Returns True if successful, or False if the document is a duplicate.

        Args:
        - page_content: The content of the document.
        - metadata: The metadata of the document.

        Returns:
        True if the document was added, False if it was a duplicate.
        """
        if not isinstance(page_content, str) or not isinstance(metadata, str):
            raise TypeError("Both page_content and metadata must be strings.")

        query = """INSERT INTO documents(page_content, metadata)
                VALUES (?, ?);"""
        try:
            self.execute_query(query, (page_content, metadata))
            return True
        except sqlite3.IntegrityError:
            logger.info("Duplicate document not added.")
            return False
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise

    def get_document(self, id: int) -> dict:
        """
        Retrieves a document from the database by its ID.

        Args:
        - id: The ID of the document to retrieve.

        Returns:
        A dictionary containing the document data.
        """
        if not isinstance(id, int):
            raise TypeError("ID must be an integer.")

        query = "SELECT * FROM documents WHERE id = ?;"
        try:
            result = self.execute_read_query(query, (id,))
            if result:
                columns = ["id", "page_content", "metadata"]
                return dict(zip(columns, result[0]))
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to get document with ID {id}: {e}")
            raise

    def delete_document(self, id: int) -> bool:
        """
        Deletes a document from the database by its ID.

        Args:
        - id: The ID of the document to delete.

        Returns:
        True if the document was deleted, False otherwise.
        """
        if not isinstance(id, int):
            raise TypeError("ID must be an integer.")

        query = "DELETE FROM documents WHERE id = ?;"
        try:
            affected_rows = self.execute_query(query, (id,))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Failed to delete document with ID {id}: {e}")
            raise
