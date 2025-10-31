from uuid import uuid4

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text

from sqlalchemy.orm import relationship
import datetime

from sqlalchemy_utils import UUIDType
from db.base_class import Base


class Post(Base):
    uid = Column(UUIDType, default=uuid4, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    title = Column(String)
    image = Column(String)
    content = Column(Text)
    owner_uid = Column(UUIDType, ForeignKey("user.uid"))
    owner = relationship("User", back_populates="post")


class Comments(Base):
    uid = Column(UUIDType, default=uuid4, primary_key=True)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    content = Column(Text)
    post_uid = Column(UUIDType, ForeignKey('post.uid'))
    owner_uid = Column(UUIDType, ForeignKey("user.uid"))

