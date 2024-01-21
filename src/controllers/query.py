from typing import Optional, List, Dict, Any
from src.global_initializer import get_docstore


async def search_documents(
    query: str,
    k: int = 5,
    metadata: Optional[Dict[str, Any]] = None
) -> List[Dict]:
    search_result = await get_docstore().search(
        query=query,
        k=k,
        metadata=metadata
    )
    return [
        v.to_dict()
        for v in search_result
    ]
