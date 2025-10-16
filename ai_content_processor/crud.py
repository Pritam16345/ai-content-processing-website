# backend/crud.py (User Accounts Update)

from sqlalchemy.orm import Session
import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- User Functions ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, name: str, email: str, password: str):
    hashed_password = pwd_context.hash(password)
    db_user = models.User(name=name, email=email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- Content Source Functions ---
def get_sources_by_owner(db: Session, owner_id: int):
    return db.query(models.ContentSource).filter(models.ContentSource.owner_id == owner_id).all()

def get_content_by_source_and_owner(db: Session, owner_id: int, source_identifier: str):
    return db.query(models.ContentSource).filter(
        models.ContentSource.owner_id == owner_id,
        models.ContentSource.source_identifier == source_identifier
    ).first()

def create_content_source(db: Session, source_identifier: str, source_type: str, content: str, title: str, owner_id: int):
    db_content = models.ContentSource(
        source_identifier=source_identifier,
        source_type=source_type,
        content=content,
        title=title,
        owner_id=owner_id
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content

def delete_content_source_by_id(db: Session, source_id: int, owner_id: int):
    db_content = db.query(models.ContentSource).filter(
        models.ContentSource.id == source_id,
        models.ContentSource.owner_id == owner_id
    ).first()
    if db_content:
        db.delete(db_content)
        db.commit()
        return db_content
    return None