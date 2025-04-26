from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import uuid

from lib.db.models import APIKey


def create_api_key(db: Session, name: str, user_id: str = None):
    api_key = APIKey(name=name, key=str(uuid.uuid4()), user_id=user_id)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


def get_api_key_by_key(db: Session, key: str):
    return db.query(APIKey).filter(APIKey.key == key).first()


def get_api_keys(db: Session, skip: int = 0, limit: int = 100, user_id: str = None):
    query = db.query(APIKey)
    if user_id:
        query = query.filter(APIKey.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def update_api_key_last_used(db: Session, api_key: APIKey):
    api_key.last_used_at = datetime.utcnow()
    db.commit()
    db.refresh(api_key)
    return api_key


def update_api_key_status(db: Session, key_id: str, is_active: bool):
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if api_key:
        api_key.is_active = is_active
        db.commit()
        db.refresh(api_key)
    return api_key


def delete_api_key(db: Session, key_id: str):
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if api_key:
        db.delete(api_key)
        db.commit()
    return api_key
