from . import Database


class Document:
    def __init__(self, db: Database):
        self.db = db

    def add_document(self, content, source_info):
        query = """INSERT INTO documents(content, source_info)
                   VALUES (?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                   content = excluded.content,
                   source_info = excluded.source_info;"""
        return self.db.execute_query(query, (content, source_info))

    def get_document(self, id):
        query = "SELECT * FROM documents WHERE id = ?;"
        return self.db.execute_read_query(query, (id,))

    def delete_document(self, id):
        query = "DELETE FROM documents WHERE id = ?;"
        return self.db.execute_query(query, (id,))
