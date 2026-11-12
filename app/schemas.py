from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _clean(value):
    """Rimuove gli spazi; una stringa vuota diventa None."""
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


OptText = Annotated[Annotated[str, Field(max_length=500)] | None, BeforeValidator(_clean)]
Name = Annotated[str, BeforeValidator(_clean), Field(min_length=1, max_length=200)]


class LoginIn(BaseModel):
    username: str  # username oppure email
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str


class LookupIn(BaseModel):
    name: Name


class LookupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ItemIn(BaseModel):
    name: Name
    category_id: int | None = None
    room_id: int | None = None
    container: OptText = None
    position: OptText = None
    notes: OptText = None
    to_find: bool = False


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    category_id: int | None
    category_name: str | None
    room_id: int | None
    room_name: str | None
    container: str | None
    position: str | None
    notes: str | None
    to_find: bool
    created_by: str | None
    updated_by: str | None
    created_at: datetime
    updated_at: datetime
