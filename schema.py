import random
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


STATE_NOT_STARTED = "not-started"
STATE_LIVE = "live"
STATE_VOD = "vod"
STATE_EXPIRED = "expired"


def generate_id():
    return str(uuid4())


def generate_key(size=11):
    valid_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    key = ""
    for i in range(size):
        key += random.choice(valid_chars)
    return key


class Model(Base):
    __abstract__ = True
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=None, nullable=False)
    deleted_at = Column(DateTime, default=None, nullable=True)


class Ping(Model):
    __tablename__ = "ping"


class Live(Model):
    __tablename__ = "lives"

    title = Column(String, unique=False, index=True, nullable=False)
    state = Column(String, nullable=False)
    password = Column(String, nullable=True)
    expires_in = Column(Integer, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, unique=False, nullable=False)
    stream_key = Column(String, unique=True, index=True, nullable=False)
    watch_key = Column(String, unique=True, index=True, nullable=False)

    duration = Column(Integer, nullable=False)
    viewer_count = Column(Integer, nullable=False)

    user = relationship("User", back_populates="lives")
    checkin = relationship("Checkin", back_populates="live")


class Checkin(Model):
    __tablename__ = "checkin"
    live_id = Column(String, ForeignKey("lives.id"), index=True, unique=False, nullable=False)
    nickname = Column(String, index=True, unique=False, nullable=False)

    live = relationship("Live", back_populates="checkin")


class User(Model):
    __tablename__ = "users"

    username = Column(String, unique=False, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    lives = relationship("Live", order_by=Live.id, back_populates="user")
