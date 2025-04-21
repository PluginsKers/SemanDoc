from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel, Field
import uvicorn

from lib.retrieval.vectorstore import VectorStore
from lib.retrieval.schemas import Document, Metadata, MetadataFilter

app = FastAPI(
    title="SemanDoc API",
    description="Document retrieval and search API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = VectorStore(
    folder_path="./vector_store",
    model_name="./models/embedders/m3e-base",
    device="cpu",
)


class DocumentBase(BaseModel):
    content: str
    tags: Optional[List[str]] = Field(default_factory=list)
    categories: Optional[List[str]] = Field(default_factory=list)


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: str

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str
    k: int = 5
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class SearchResult(BaseModel):
    results: List[DocumentResponse]


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
        id=doc.metadata.ids, content=doc.content, tags=tags, categories=categories
    )


# API路由
@app.get("/")
async def root():
    return {"message": "Welcome to the VectorStore API"}


@app.post("/documents/", response_model=DocumentResponse)
async def create_document(document: DocumentCreate):
    try:
        doc = Document(
            content=document.content,
            metadata=Metadata(tags=document.tags, categories=document.categories),
        )
        doc_id = doc.metadata.ids

        vector_store.add_documents([doc])
        vector_store.save_index()

        for key, stored_doc in vector_store.docstore.items():
            if stored_doc.metadata.ids == doc_id:
                return document_to_response(stored_doc)

        return document_to_response(doc)
    except Exception as e:
        print(f"Error creating document: {e}")
        raise HTTPException(status_code=500, detail=f"Create document failed: {str(e)}")


@app.post("/documents/batch/", response_model=List[DocumentResponse])
async def create_documents_batch(documents: List[DocumentCreate]):
    try:
        docs = []
        doc_ids = []
        for doc_data in documents:
            doc = Document(
                content=doc_data.content,
                metadata=Metadata(tags=doc_data.tags, categories=doc_data.categories),
            )
            docs.append(doc)
            doc_ids.append(doc.metadata.ids)

        vector_store.add_documents(docs)
        vector_store.save_index()

        result_docs = []
        for doc_id in doc_ids:
            for key, stored_doc in vector_store.docstore.items():
                if stored_doc.metadata.ids == doc_id:
                    result_docs.append(stored_doc)
                    break
            else:
                for doc in docs:
                    if doc.metadata.ids == doc_id:
                        result_docs.append(doc)
                        break

        return [document_to_response(doc) for doc in result_docs]
    except Exception as e:
        print(f"Error creating documents batch: {e}")
        raise HTTPException(
            status_code=500, detail=f"Create documents batch failed: {str(e)}"
        )


@app.get("/documents/{document_id}", response_model=DocumentResponse)
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
        print(f"Error retrieving document: {e}")
        raise HTTPException(status_code=500, detail=f"Get document failed: {str(e)}")


@app.delete("/documents/{document_id}", response_model=DocumentResponse)
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
        vector_store.save_index()

        return result_doc
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Delete document failed: {str(e)}")


@app.post("/documents/search/", response_model=SearchResult)
async def search_documents(search_query: SearchQuery):
    try:
        metadata_filter = None
        if search_query.tags or search_query.categories:
            metadata_filter = MetadataFilter(
                tags=search_query.tags, categories=search_query.categories
            )

        results = vector_store.search(
            query=search_query.query, k=search_query.k, metadata_filter=metadata_filter
        )

        return SearchResult(results=[document_to_response(doc) for doc in results])
    except Exception as e:
        print(f"Error searching documents: {e}")
        raise HTTPException(
            status_code=500, detail=f"Search documents failed: {str(e)}"
        )


@app.get("/documents/", response_model=List[DocumentResponse])
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
        print(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=f"List documents failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
