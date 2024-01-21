from src.global_initializer import get_docstore

async def search_documents(query: str, k: int = 5, filter: dict = None) -> list:
    query_result = await get_docstore().search(query, k, filter)
    return [
        v.to_dict()
        for v in query_result
    ]
