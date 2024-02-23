from typing import Union, Optional, List, Tuple
from src.modules.document import Document

from src import get_docstore


class DatabaseEditError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


async def add_document(
    data: dict, comment: Optional[str] = None
) -> Union[Tuple[List[Document]], str]:
    if comment:
        print(comment)

    metadata = data["metadata"]
    add_result = await get_docstore().add_documents(
        [Document(page_content=data["page_content"], metadata=metadata)]
    )
    if len(add_result) <= 0:
        raise DatabaseEditError("Failed to add document to the database.")

    return tuple([add_result])


def delete_documents_by_ids(
    ids_to_delete: List[int], comment: Optional[str] = None
) -> Union[Tuple[int, int], str]:
    if comment:
        print(comment)

    removal_result = get_docstore().remove_documents_by_ids(ids_to_delete)

    return removal_result


def delete_documents_by_id(
    id_to_delete: List[str], comment: Optional[str] = None
) -> Union[Tuple[int, int], str]:
    if comment:
        print(comment)

    removal_result = get_docstore().remove_documents_by_id(id_to_delete)

    return removal_result


def delete_documents_by_tags(
    tags_to_delete: List[str], comment: Optional[str] = None
) -> Union[Tuple[int, int], str]:
    if comment:
        print(comment)

    removal_result = get_docstore().remove_documents_by_tags(tags_to_delete)

    return removal_result
