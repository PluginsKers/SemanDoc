from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from lib.db.database import get_db
from lib.db.crud import (
    create_api_key,
    get_api_keys,
    update_api_key_status,
    delete_api_key,
)
from lib.auth.dependencies import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class APIKeyBase(BaseModel):
    name: str


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyResponse(APIKeyBase):
    id: str
    key: str
    is_active: bool

    class Config:
        from_attributes = True


class APIKeyList(BaseModel):
    keys: List[APIKeyResponse]
    total: int


@router.post(
    "/",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a new API key",
)
async def create_new_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_api_key),
):
    """Create a new API key"""
    try:
        # TODO: Verify user permissions after user system implementation

        api_key = create_api_key(db, name=api_key_data.name, user_id=user_id)
        logger.info(f"Created new API key: {api_key.name}")
        return api_key
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        )


@router.get("/", response_model=APIKeyList, description="Get all API keys")
async def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_api_key),
):
    """Get all API keys"""
    try:
        # TODO: Verify user permissions after user system implementation
        # Temporarily show all keys

        api_keys = get_api_keys(db, skip=skip, limit=limit)
        total = len(api_keys)
        return APIKeyList(keys=api_keys, total=total)
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key list: {str(e)}",
        )


@router.put(
    "/{key_id}/status",
    response_model=APIKeyResponse,
    description="Update API key status",
)
async def update_api_key_activation(
    key_id: str,
    is_active: bool,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_api_key),
):
    """Update API key status"""
    try:
        # TODO: Verify user permissions after user system implementation

        api_key = update_api_key_status(db, key_id=key_id, is_active=is_active)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {key_id} does not exist",
            )

        logger.info(f"Updated API key status: {api_key.name} -> {is_active}")
        return api_key
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error updating API key status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API key status: {str(e)}",
        )


@router.delete(
    "/{key_id}", status_code=status.HTTP_204_NO_CONTENT, description="Delete API key"
)
async def remove_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_api_key),
):
    """Delete API key"""
    try:
        # TODO: Verify user permissions after user system implementation

        api_key = delete_api_key(db, key_id=key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {key_id} does not exist",
            )

        logger.info(f"Deleted API key: {api_key.name}")
        return None
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}",
        )
