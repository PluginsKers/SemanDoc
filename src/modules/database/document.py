from src import get_database_instance


class Document:
    def __init__(self):
        self.db = get_database_instance()

    def add_document(self, page_content: str, metadata: str):
        if not isinstance(page_content, str) or not isinstance(metadata, str):
            raise TypeError("Both page_content and metadata must be strings.")

        query = """INSERT INTO documents(page_content, metadata)
                   VALUES (?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   page_content = excluded.page_content,
                   metadata = excluded.metadata;"""
        return self.db.execute_query(query, (page_content, metadata))

    def get_document(self, id: int):
        query = "SELECT * FROM documents WHERE id = ?;"
        return self.db.execute_read_query(query, (id,))

    def delete_document(self, id: int):
        query = "DELETE FROM documents WHERE id = ?;"
        return self.db.execute_query(query, (id,))
