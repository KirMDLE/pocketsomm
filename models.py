from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base  # или как у тебя называется Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    favorites = relationship("FavoriteWine", back_populates="user", cascade="all, delete-orphan")

class FavoriteWine(Base):
    __tablename__ = "favorite_wines"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    wine_id = Column(Integer)  # id или уникальный идентификатор вина из API
    user = relationship("User", back_populates="favorites")

    __table_args__ = (UniqueConstraint("user_id", "wine_id", name="_user_wine_uc"),)

