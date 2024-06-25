import logging
import pytz
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.modules.database.sqlite import DatabaseManager

logger = logging.getLogger(__name__)


class Document(DatabaseManager):
    def __init__(self, db: DatabaseManager):
        """
        Initialize the Document class with a database connection.

        Args:
            db: A Database instance.
        """
        super().__init__(db.db_path)

    def add_document(self, ids: str, page_content: str, metadata: str, user_id: Optional[int] = None, desc: str = 'Added.') -> bool:
        """
        Adds a new document to the database along with an initial document history record.

        Args:
            ids: The hashed UUID4 identifier.
            page_content: The content of the document.
            metadata: The metadata of the document.
            user_id: The ID of the user adding the document.
            desc: Description of the document addition.

        Returns:
            bool: True if the document was added successfully, False otherwise.
        """
        document_query = "INSERT INTO documents(ids, page_content, metadata) VALUES (?, ?, ?);"
        history_query = """INSERT INTO documents_records(document_id, editor_id, edit_time, edit_description) 
                           VALUES (?, ?, ?, ?);"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("BEGIN;")

            document_id = self.execute_query(
                document_query, (ids, page_content, metadata))
            if document_id is None:
                raise Exception("Failed to insert the document.")

            edit_time = datetime.now().astimezone(pytz.utc).astimezone(
                pytz.timezone('Asia/Shanghai')
            ).strftime("%Y-%m-%d %H:%M:%S")
            history_result = self.execute_query(
                history_query, (document_id, user_id, edit_time, desc))
            if history_result is None:
                raise Exception("Failed to insert the document history.")

            conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.info("Duplicate document not added.")
            return False
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction: {rollback_error}")
            return False

    def get_document_by_id(self, id: int) -> Dict[str, Any]:
        """
        Retrieve a document by its ID.

        Args:
            id: The ID of the document.

        Returns:
            dict: The document details.
        """
        if not isinstance(id, int):
            raise TypeError("ID must be an integer.")

        query = "SELECT * FROM documents WHERE id = ?;"
        try:
            result = self.execute_read_query(query, (id,))
            if result:
                columns = ["id", "ids", "page_content", "metadata"]
                return dict(zip(columns, result[0]))
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to get document with ID {id}: {e}")
            raise

    def get_document_by_ids(self, ids: str) -> Dict[str, Any]:
        """
        Retrieve a document by its UUID4.

        Args:
            ids: The hashed UUID4 identifier of the document.

        Returns:
            dict: The document details.
        """
        if not isinstance(ids, str):
            raise TypeError("IDs must be a string.")

        query = "SELECT * FROM documents WHERE ids = ?;"
        try:
            result = self.execute_read_query(query, (ids,), fetchone=True)
            if result:
                columns = ["id", "ids", "page_content", "metadata"]
                return dict(zip(columns, result))
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to get document with IDs {ids}: {e}")
            raise

    def delete_document_by_id(self, id: int, user_id: Optional[int] = None, desc: str = 'Deleted.') -> bool:
        """
        Delete a document by its ID and log the deletion in document history.

        Args:
            id: The ID of the document to delete.
            user_id: The ID of the user performing the deletion.
            desc: Description of the deletion action.

        Returns:
            bool: True if the document was deleted successfully, False otherwise.
        """
        history_query = """INSERT INTO documents_records(document_id, editor_id, edit_time, edit_description) 
                        VALUES (?, ?, ?, ?);"""
        delete_query = "DELETE FROM documents WHERE id = ?;"
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("BEGIN;")

            edit_time = datetime.now().astimezone(pytz.utc).astimezone(
                pytz.timezone('Asia/Shanghai')
            ).strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(history_query, (id, user_id, edit_time, desc))

            # affected_rows = self.execute_query(delete_query, (id,))
            # if affected_rows == 0:
            #     raise Exception("Failed to delete the document.")

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction: {rollback_error}")
            return False

    def delete_document_by_ids(self, ids: str, user_id: Optional[int] = None, desc: str = 'Deleted.') -> bool:
        """
        Delete a document by its UUID4 and log the deletion in document history.

        Args:
            ids: The hashed UUID4 identifier of the document to delete.
            user_id: The ID of the user performing the deletion.
            desc: Description of the deletion action.

        Returns:
            bool: True if the document was deleted successfully, False otherwise.
        """
        document = self.get_document_by_ids(ids)
        if not document:
            return False

        history_query = """INSERT INTO documents_records(document_id, editor_id, edit_time, edit_description) 
                        VALUES (?, ?, ?, ?);"""
        delete_query = "DELETE FROM documents WHERE ids = ?;"
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("BEGIN;")

            edit_time = datetime.now().astimezone(pytz.utc).astimezone(
                pytz.timezone('Asia/Shanghai')
            ).strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(
                history_query, (document["id"], user_id, edit_time, desc))

            # affected_rows = self.execute_query(delete_query, (ids,))
            # if affected_rows == 0:
            #     raise Exception("Failed to delete the document.")

            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting document by UUID4 {ids}: {e}")
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction: {rollback_error}")
            return False

    def get_documents_records(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve the records of documents list.

        Args:
            limit (int): Limit the number of records returned.

        Returns:
            list: A list of records records for the document.
        """
        query = "SELECT * FROM documents_records ORDER BY edit_time DESC"
        if limit is not None:
            query += f" LIMIT {limit};"
        else:
            query += ";"

        try:
            result = self.execute_read_query(query)
            columns = ["id", "document_id", "editor_id",
                       "edit_time", "edit_description"]
            return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            logger.error(f"Failed to get documents history: {e}")
            raise
