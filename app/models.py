from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    room_id: Mapped[int | None] = mapped_column(ForeignKey("rooms.id"))
    container: Mapped[str | None]
    position: Mapped[str | None]
    notes: Mapped[str | None]
    to_find: Mapped[bool] = mapped_column(default=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())

    category: Mapped[Category | None] = relationship(lazy="joined")
    room: Mapped[Room | None] = relationship(lazy="joined")
    created_by_user: Mapped[User | None] = relationship(foreign_keys=[created_by_id], lazy="joined")
    updated_by_user: Mapped[User | None] = relationship(foreign_keys=[updated_by_id], lazy="joined")

    @property
    def category_name(self) -> str | None:
        return self.category.name if self.category else None

    @property
    def room_name(self) -> str | None:
        return self.room.name if self.room else None

    @property
    def created_by(self) -> str | None:
        return self.created_by_user.username if self.created_by_user else None

    @property
    def updated_by(self) -> str | None:
        return self.updated_by_user.username if self.updated_by_user else None
