from fastapi import APIRouter, HTTPException, Header, Query, Depends, UploadFile, File
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import logging
import time
from io import BytesIO
import pandas as pd
from fastapi.responses import StreamingResponse

from lib.retrieval.vectorstore import VectorStore
from lib.retrieval.schemas import Document, Metadata, MetadataFilter
from lib.auth.dependencies import get_api_key

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
    async def create_document(
        document: DocumentCreate, user_id: Optional[str] = Depends(get_api_key)
    ):
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
        user_id: Optional[str] = Depends(get_api_key),
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
    async def create_documents_batch(
        documents: List[DocumentCreate], user_id: Optional[str] = Depends(get_api_key)
    ):
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
    async def get_document(
        document_id: str, user_id: Optional[str] = Depends(get_api_key)
    ):
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
    async def delete_document(
        document_id: str, user_id: Optional[str] = Depends(get_api_key)
    ):
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
    async def search_documents(
        search_query: SearchQuery, user_id: Optional[str] = Depends(get_api_key)
    ):
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
        user_id: Optional[str] = Depends(get_api_key),
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
    async def update_document(
        document_id: str,
        document: DocumentCreate,
        user_id: Optional[str] = Depends(get_api_key),
    ):
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
    async def get_document_stats(user_id: Optional[str] = Depends(get_api_key)):
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
    async def save_vector_store(user_id: Optional[str] = Depends(get_api_key)):
        try:
            logger.info("Manual save triggered via API")
            vector_store.save_index()
            return SaveResponse(success=True, message="Vector store saved successfully")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise HTTPException(
                status_code=500, detail=f"Save vector store failed: {str(e)}"
            )

    @router.get(
        "/export/xlsx",
        description="Export documents as Excel file",
    )
    async def export_documents_xlsx(
        skip: int = 0,
        limit: int = 1000,
        tag: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = Depends(get_api_key),
    ):
        try:
            filters = []
            if tag:
                filters.append(lambda doc: tag in doc.metadata.tags)
            if category:
                filters.append(lambda doc: category in doc.metadata.categories)

            # Get documents and apply filters
            documents = []
            for doc_id, doc in vector_store.docstore.items():
                if all(f(doc) for f in filters) or not filters:
                    documents.append(doc)

            # Apply pagination
            documents = documents[skip : skip + limit]

            # Format start time
            def format_time(timestamp):
                if timestamp:
                    from datetime import datetime

                    # Use datetime object instead of strftime to avoid locale issues
                    dt = datetime.fromtimestamp(timestamp)
                    return f"{dt.year}年{dt.month}月{dt.day}日 {dt.hour:02d}:{dt.minute:02d}"
                return ""

            # Create data with syntax sugar
            data = []
            for doc in documents:
                # Format tags and categories as comma-separated strings
                tags_str = ",".join(str(tag) for tag in doc.metadata.tags)
                categories_str = ",".join(str(cat) for cat in doc.metadata.categories)

                # Format start time
                start_time = format_time(doc.metadata.start_time)

                # End time is not specified in the metadata schema, so we'll leave it empty
                end_time = ""

                # Create syntax sugar
                syntax_sugar = f"<{start_time};{categories_str};{tags_str};{end_time}>"

                # Add to content
                content_with_sugar = f"{doc.content}\n{syntax_sugar}"

                data.append([content_with_sugar])

            # Create DataFrame with only one column and no header
            df = pd.DataFrame(data)

            # Create Excel file without header
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, header=False)
            output.seek(0)

            # Return the Excel file as a downloadable attachment
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=documents.xlsx"},
            )
        except Exception as e:
            logger.error(f"Error exporting documents as XLSX: {e}")
            raise HTTPException(
                status_code=500, detail=f"Export documents as XLSX failed: {str(e)}"
            )

    @router.post(
        "/upload/xlsx",
        response_model=List[DocumentResponse],
        description="Upload and parse Excel file to add documents",
    )
    async def upload_documents_xlsx(
        file: UploadFile = File(...),
        user_id: Optional[str] = Depends(get_api_key),
    ):
        try:
            logger.info(f"Received file upload: {file.filename}")

            # Check if file is an Excel file
            if not file.filename.endswith((".xlsx", ".xls")):
                raise HTTPException(
                    status_code=400,
                    detail="Only Excel files (.xlsx, .xls) are supported",
                )

            # Read Excel file
            try:
                content = await file.read()
                excel_data = BytesIO(content)
            except Exception as e:
                logger.error(f"Error reading uploaded file: {e}")
                raise HTTPException(
                    status_code=400, detail=f"Error reading uploaded file: {str(e)}"
                )

            try:
                # Try to read without headers since we expect no headers
                df = pd.read_excel(excel_data, header=None)
            except Exception as e:
                logger.error(f"Error parsing Excel file: {e}")
                raise HTTPException(
                    status_code=400, detail=f"Invalid Excel file format: {str(e)}"
                )

            if df.empty:
                raise HTTPException(status_code=400, detail="Excel file is empty")

            # Process rows and extract syntax sugar
            documents = []
            for _, row in df.iterrows():
                # Get content from first column
                if len(row) == 0 or pd.isna(row[0]):
                    continue

                content_with_sugar = str(row[0]).strip()

                # Extract content and syntax sugar
                content = content_with_sugar
                tags = []
                categories = []
                start_time = None
                end_time = None

                # Find syntax sugar pattern <start_time;categories;tags;end_time>
                import re

                syntax_pattern = r"<([^;]*);([^;]*);([^;]*);([^;>]*)>"
                match = re.search(syntax_pattern, content_with_sugar)

                if match:
                    # Remove syntax sugar from content
                    content = content_with_sugar.replace(match.group(0), "").strip()

                    # Extract metadata from syntax sugar
                    start_time_str = match.group(1).strip()
                    categories_str = match.group(2).strip()
                    tags_str = match.group(3).strip()
                    end_time_str = match.group(4).strip()

                    # Parse categories
                    if categories_str:
                        categories = [
                            cat.strip()
                            for cat in categories_str.split(",")
                            if cat.strip()
                        ]

                    # Parse tags
                    if tags_str:
                        tags = [
                            tag.strip() for tag in tags_str.split(",") if tag.strip()
                        ]

                    # Parse start time
                    if start_time_str:
                        try:
                            import time
                            from datetime import datetime

                            # Parse Chinese date format
                            start_time = datetime.strptime(
                                start_time_str, "%Y年%m月%d日 %H:%M"
                            ).timestamp()
                        except Exception as e:
                            logger.warning(
                                f"Could not parse start time: {start_time_str}, error: {e}"
                            )

                    # Parse end time if provided
                    if end_time_str:
                        try:
                            from datetime import datetime

                            # Calculate valid_time as seconds from now until end_time
                            end_timestamp = datetime.strptime(
                                end_time_str, "%Y年%m月%d日 %H:%M"
                            ).timestamp()

                            # If we have both start and end time, calculate valid_time
                            if start_time:
                                valid_time = int(end_timestamp - start_time)
                                if valid_time <= 0:
                                    valid_time = (
                                        -1
                                    )  # No expiration if end time <= start time
                            else:
                                # If no start time, just use current time
                                valid_time = int(end_timestamp - time.time())
                                if valid_time <= 0:
                                    valid_time = -1  # No expiration if already passed
                        except Exception as e:
                            logger.warning(
                                f"Could not parse end time: {end_time_str}, error: {e}"
                            )
                            valid_time = -1  # No expiration
                    else:
                        valid_time = -1  # No expiration

                # Create document
                metadata = Metadata(
                    tags=tags,
                    categories=categories,
                    start_time=start_time,
                    valid_time=valid_time if "valid_time" in locals() else -1,
                )

                doc = Document(content=content, metadata=metadata)
                documents.append(doc)

            if not documents:
                raise HTTPException(
                    status_code=400, detail="No valid documents found in the Excel file"
                )

            # Add documents to vector store
            logger.info(f"Adding {len(documents)} documents from Excel file")
            added_docs = vector_store.add_documents(documents)

            return [document_to_response(doc) for doc in added_docs]
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            logger.error(f"Error uploading Excel file: {e}")
            raise HTTPException(
                status_code=500, detail=f"Upload Excel file failed: {str(e)}"
            )

    return router
