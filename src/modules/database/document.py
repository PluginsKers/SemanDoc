import logging
import sqlite3
from datetime import datetime
from typing import Optional

from src.modules.database.sqlite import Database

logger = logging.getLogger(__name__)


class Document(Database):
    def __init__(self, db: Database):
        """
        Initialize the Document class with a database connection.

        Args:
            db: A Database instance.
        """
        super().__init__(db.db_file)

    def add_document(self, page_content: str, metadata: str, user_id: Optional[int] = None, desc: str = 'Document added.') -> bool:
        """
        Adds a new document to the database along with an initial document history record.
        Args:
            page_content: The content of the document.
            metadata: The metadata of the document.
            user_id: The ID of the user adding the document.
        Returns:
            bool: True if the document was added, False if it was a duplicate.
        """
        if not all(isinstance(arg, str) for arg in [page_content, metadata]) or not isinstance(user_id, int):
            raise TypeError(
                "page_content and metadata must be strings, and user_id must be an integer.")

        document_query = "INSERT INTO documents(page_content, metadata) VALUES (?, ?);"
        history_query = """INSERT INTO document_history(document_id, editor_id, edit_time, edit_description) 
                           VALUES (?, ?, ?, ?);"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Begin a transaction
            cursor.execute("BEGIN;")

            # Insert the document and get its ID
            document_id = self.execute_query(
                document_query, (page_content, metadata))
            if document_id is None:
                raise Exception("Failed to insert the document.")

            # Get current time in the required format
            edit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insert the initial history record
            history_result = self.execute_query(
                history_query, (document_id, user_id, edit_time, desc))
            if history_result is None:
                raise Exception("Failed to insert the document history.")

            # Commit the transaction
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.info("Duplicate document not added.")
            return False
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            # Attempt to rollback in case of failure
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction: {rollback_error}")
            return False

    def get_document(self, id: int) -> dict:
        """
        Retrieves a document from the database by its ID.

        Args:
            id: The ID of the document to retrieve.

        Returns:
            dict: A dictionary containing the document data.
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

    def delete_document(self, id: str, user_id: Optional[int] = None, desc: str = 'Document deleted.') -> bool:
        """
        Deletes a document from the database by its ID and records the deletion in the document history.

        Args:
            id: The ID of the document to delete.
            user_id: The ID of the user deleting the document.
            desc: A description of the delete operation.

        Returns:
            bool: True if the document was deleted, False otherwise.
        """
        if not isinstance(id, int):
            raise TypeError("ID must be an integer.")

        history_query = """INSERT INTO document_history(document_id, editor_id, edit_time, edit_description) 
                        VALUES (?, ?, ?, ?);"""
        delete_query = "DELETE FROM documents WHERE id = ?;"
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Begin a transaction
            cursor.execute("BEGIN;")

            # Insert the delete history record
            edit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(
                history_query, (id, user_id, edit_time, desc))

            # Delete the document
            affected_rows = self.execute_query(delete_query, (id,))
            if affected_rows == 0:
                raise Exception("Failed to delete the document.")

            # Commit the transaction
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            # Attempt to rollback in case of failure
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction: {rollback_error}")
            return False
