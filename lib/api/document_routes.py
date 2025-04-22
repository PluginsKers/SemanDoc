from fastapi import APIRouter, HTTPException, Header, Query
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import logging

from lib.retrieval.vectorstore import VectorStore
from lib.retrieval.schemas import Document, Metadata, MetadataFilter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


class MetadataBase(BaseModel):
    ids: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    categories: Optional[List[str]] = Field(default_factory=list)


class DocumentBase(BaseModel):
    content: str
    metadata: MetadataBase


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str
    k: int = 5
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    score_threshold: Optional[float] = None


class StatsResponse(BaseModel):
    total_documents: int
    unique_tags: List[str]
    unique_categories: List[str]
    documents_per_tag: Dict[str, int]
    documents_per_category: Dict[str, int]


class SaveResponse(BaseModel):
    success: bool
    message: str


def document_to_response(doc: Document) -> DocumentResponse:
    tags = []
    for tag in doc.metadata.tags:
        if isinstance(tag, list):
            tags.extend([str(t) for t in tag])
        else:
            tags.append(str(tag))

    categories = []
    for cat in doc.metadata.categories:
        if isinstance(cat, list):
            categories.extend([str(c) for c in cat])
        else:
            categories.append(str(cat))

    return DocumentResponse(
        content=doc.content,
        metadata=MetadataBase(ids=doc.metadata.ids, tags=tags, categories=categories),
    )


def init_routes(vector_store: VectorStore):

    @router.post(
        "/",
        response_model=DocumentResponse,
        description="Create a new document in the vector store",
    )
    async def create_document(document: DocumentCreate):
        try:
            doc = Document(
                content=document.content,
                metadata=Metadata(
                    tags=document.metadata.tags, categories=document.metadata.categories
                ),
            )

            added_docs = vector_store.add_documents([doc])

            if not added_docs:
                raise HTTPException(
                    status_code=409, detail="Document is a duplicate and was not added"
                )

            return document_to_response(added_docs[0])
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise HTTPException(
                status_code=500, detail=f"Create document failed: {str(e)}"
            )

    @router.get(
        "/webhook",
        response_model=DocumentResponse,
        description="Webhook endpoint for quickly creating documents with minimal data",
    )
    async def webhook_create_document(
        content: str,
        tags: Optional[List[str]] = Query(default_factory=list),
        categories: Optional[List[str]] = Query(default_factory=list),
    ):
        try:
            doc = Document(
                content=content,
                metadata=Metadata(tags=tags, categories=categories),
            )

            logger.info("Processing webhook document creation request")
            added_docs = vector_store.add_documents([doc])

            if not added_docs:
                raise HTTPException(
                    status_code=409, detail="Document is a duplicate and was not added"
                )

            return document_to_response(added_docs[0])
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            logger.error(f"Error creating document via webhook: {e}")
            raise HTTPException(
                status_code=500, detail=f"Webhook document creation failed: {str(e)}"
            )

    @router.post(
        "/batch/",
        response_model=List[DocumentResponse],
        description="Create multiple documents in a single batch operation",
    )
    async def create_documents_batch(documents: List[DocumentCreate]):
        try:
            docs = []
            for doc_data in documents:
                doc = Document(
                    content=doc_data.content,
                    metadata=Metadata(
                        tags=doc_data.metadata.tags,
                        categories=doc_data.metadata.categories,
                    ),
                )
                docs.append(doc)

            added_docs = vector_store.add_documents(docs)

            return [document_to_response(doc) for doc in added_docs]
        except Exception as e:
            logger.error(f"Error creating documents batch: {e}")
            raise HTTPException(
                status_code=500, detail=f"Create documents batch failed: {str(e)}"
            )

    @router.get(
        "/{document_id}",
        response_model=DocumentResponse,
        description="Retrieve a specific document by its ID",
    )
    async def get_document(document_id: str):
        try:
            for key, doc in vector_store.docstore.items():
                if doc.metadata.ids == document_id:
                    return document_to_response(doc)

            raise HTTPException(
                status_code=404, detail=f"Document ID {document_id} does not exist"
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            logger.error(f"Error retrieving document: {e}")
            raise HTTPException(
                status_code=500, detail=f"Get document failed: {str(e)}"
            )

    @router.delete(
        "/{document_id}",
        response_model=DocumentResponse,
        description="Delete a document by its ID",
    )
    async def delete_document(document_id: str):
        try:
            doc_found = None
            for key, doc in vector_store.docstore.items():
                if doc.metadata.ids == document_id:
                    doc_found = doc
                    break

            if not doc_found:
                raise HTTPException(
                    status_code=404, detail=f"Document ID {document_id} does not exist"
                )

            result_doc = document_to_response(doc_found)

            vector_store.delete_documents_by_ids([document_id])

            return result_doc
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            logger.error(f"Error deleting document: {e}")
            raise HTTPException(
                status_code=500, detail=f"Delete document failed: {str(e)}"
            )

    @router.post(
        "/search/",
        response_model=List[DocumentResponse],
        description="Search documents using semantic similarity and optional metadata filters",
    )
    async def search_documents(search_query: SearchQuery):
        try:
            metadata_filter = None
            if search_query.tags or search_query.categories:
                metadata_filter = MetadataFilter(
                    tags=search_query.tags, categories=search_query.categories
                )

            results = vector_store.search(
                query=search_query.query,
                k=search_query.k,
                metadata_filter=metadata_filter,
                score_threshold=search_query.score_threshold,
            )

            if not results:
                return []

            return [document_to_response(doc) for doc in results]
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise HTTPException(
                status_code=500, detail=f"Search documents failed: {str(e)}"
            )

    @router.get(
        "/",
        response_model=List[DocumentResponse],
        description="List all documents with optional filtering by tag and category",
    )
    async def list_documents(
        skip: int = 0,
        limit: int = 100,
        tag: Optional[str] = None,
        category: Optional[str] = None,
    ):
        try:
            docs = list(vector_store.docstore.values())

            if tag or category:
                filtered_docs = []
                for doc in docs:
                    tags = []
                    for t in doc.metadata.tags:
                        if isinstance(t, list):
                            tags.extend([str(item) for item in t])
                        else:
                            tags.append(str(t))

                    categories = []
                    for c in doc.metadata.categories:
                        if isinstance(c, list):
                            categories.extend([str(item) for item in c])
                        else:
                            categories.append(str(c))

                    if (not tag or tag in tags) and (
                        not category or category in categories
                    ):
                        filtered_docs.append(doc)
                docs = filtered_docs

            docs = docs[skip : skip + limit]

            return [document_to_response(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise HTTPException(
                status_code=500, detail=f"List documents failed: {str(e)}"
            )

    @router.put(
        "/{document_id}",
        response_model=DocumentResponse,
        description="Update an existing document by its ID",
    )
    async def update_document(document_id: str, document: DocumentCreate):
        try:
            doc_found = None
            for key, doc in vector_store.docstore.items():
                if doc.metadata.ids == document_id:
                    doc_found = doc
                    break

            if not doc_found:
                raise HTTPException(
                    status_code=404, detail=f"Document ID {document_id} does not exist"
                )

            vector_store.delete_documents_by_ids([document_id])

            new_doc = Document(
                content=document.content,
                metadata=Metadata(
                    ids=document_id,
                    tags=document.metadata.tags,
                    categories=document.metadata.categories,
                ),
            )

            added_docs = vector_store.add_documents([new_doc])
            if not added_docs:
                raise HTTPException(status_code=500, detail="Failed to update document")

            return document_to_response(added_docs[0])
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            logger.error(f"Error updating document: {e}")
            raise HTTPException(
                status_code=500, detail=f"Update document failed: {str(e)}"
            )

    @router.get(
        "/stats/overview",
        response_model=StatsResponse,
        description="Get statistics about documents including counts by tags and categories",
    )
    async def get_document_stats():
        try:
            docs = list(vector_store.docstore.values())

            total_documents = len(docs)

            all_tags = set()
            all_categories = set()
            tag_count = {}
            category_count = {}

            for doc in docs:
                doc_tags = []
                for tag in doc.metadata.tags:
                    if isinstance(tag, list):
                        doc_tags.extend([str(t) for t in tag])
                    else:
                        doc_tags.append(str(tag))

                for tag in doc_tags:
                    all_tags.add(tag)
                    tag_count[tag] = tag_count.get(tag, 0) + 1

                doc_categories = []
                for cat in doc.metadata.categories:
                    if isinstance(cat, list):
                        doc_categories.extend([str(c) for c in cat])
                    else:
                        doc_categories.append(str(cat))

                for category in doc_categories:
                    all_categories.add(category)
                    category_count[category] = category_count.get(category, 0) + 1

            return StatsResponse(
                total_documents=total_documents,
                unique_tags=sorted(list(all_tags)),
                unique_categories=sorted(list(all_categories)),
                documents_per_tag=tag_count,
                documents_per_category=category_count,
            )

        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            raise HTTPException(
                status_code=500, detail=f"Get document stats failed: {str(e)}"
            )

    @router.post(
        "/save",
        response_model=SaveResponse,
        description="Manually trigger saving of the vector store to persistent storage",
    )
    async def save_vector_store():
        try:
            logger.info("Manual save triggered via API")
            vector_store.save_index()
            return SaveResponse(success=True, message="Vector store saved successfully")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise HTTPException(
                status_code=500, detail=f"Save vector store failed: {str(e)}"
            )

    return router
