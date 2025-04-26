from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from lib.db.database import get_db
from lib.db.crud import get_api_key_by_key, update_api_key_last_used

logger = logging.getLogger(__name__)


async def get_api_key(
    x_api_key: Optional[str] = Header(None, description="API key for authentication"),
    db: Session = Depends(get_db),
) -> Optional[str]:
    """Verify API key and return user ID (if any)

    Currently implemented in Bypass mode, allowing access even without a valid API key.
    TODO: Remove Bypass mode after user system implementation.
    """
    if not x_api_key:
        logger.warning("No API key provided, using bypass mode")
        return None

    api_key = get_api_key_by_key(db, x_api_key)

    if not api_key:
        logger.warning("Invalid API key provided, using bypass mode")
        return None

    if not api_key.is_active:
        logger.warning("Inactive API key provided, using bypass mode")
        return None

    # Update last used time
    update_api_key_last_used(db, api_key)

    logger.info(f"Authenticated request with API key: {api_key.name}")
    return api_key.user_id
