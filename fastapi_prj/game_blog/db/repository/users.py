from sqlalchemy.orm import Session

from core.hashing import Hasher
from apps.authapp.models import User
from apps.authapp.schemas import UserCreate


def create_new_user(user: UserCreate, db: Session):
    user = User(
        username=user.username,
        email=user.email,
        hashed_password=Hasher.get_password_hash(user.password),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
