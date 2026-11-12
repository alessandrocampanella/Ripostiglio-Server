from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .models import Category, Item, Room, User
from .schemas import ItemIn, ItemOut, LoginIn, LookupIn, LookupOut, TokenOut, UserOut
from .security import LoginThrottle, create_token, current_user, verify_password

app = FastAPI(title="Ripostiglio", version="1.0.0")
throttle = LoginThrottle()

SEARCH_COLUMNS = (Item.name, Item.container, Item.position, Item.notes)


def _visible_to(user: User):
    """Oggetti pubblici, più quelli privati aggiunti dall'utente stesso."""
    return or_(Item.is_public, Item.created_by_id == user.id)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Autenticazione ----------

@app.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    identifier = data.username.strip().lower()
    client_ip = request.headers.get("CF-Connecting-IP") or (request.client.host if request.client else "")
    key = f"{identifier}|{client_ip}"
    if throttle.is_locked(key):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Troppi tentativi, riprova tra qualche minuto")

    user = db.scalar(
        select(User).where(or_(func.lower(User.username) == identifier, func.lower(User.email) == identifier))
    )
    if not verify_password(data.password, user.password_hash if user else None):
        throttle.fail(key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenziali non valide")

    throttle.reset(key)
    return TokenOut(access_token=create_token(user), username=user.username)


@app.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


# ---------- Stanze e categorie ----------

def _list_lookup(model, db: Session):
    return db.scalars(select(model).order_by(model.name)).all()


def _create_lookup(model, data: LookupIn, db: Session):
    existing = db.scalar(select(model).where(func.lower(model.name) == data.name.lower()))
    if existing:
        return existing
    row = model(name=data.name)
    db.add(row)
    db.commit()
    return row


@app.get("/rooms", response_model=list[LookupOut])
def list_rooms(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return _list_lookup(Room, db)


@app.post("/rooms", response_model=LookupOut, status_code=status.HTTP_201_CREATED)
def create_room(data: LookupIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    return _create_lookup(Room, data, db)


@app.get("/categories", response_model=list[LookupOut])
def list_categories(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return _list_lookup(Category, db)


@app.post("/categories", response_model=LookupOut, status_code=status.HTTP_201_CREATED)
def create_category(data: LookupIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    return _create_lookup(Category, data, db)


@app.get("/containers", response_model=list[str])
def list_containers(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Contenitori già usati, per l'autocompletamento nell'app."""
    return db.scalars(
        select(Item.container)
        .where(Item.container.is_not(None), _visible_to(user))
        .distinct()
        .order_by(Item.container)
    ).all()


# ---------- Oggetti ----------

def _get_item(item_id: int, db: Session, user: User) -> Item:
    item = db.get(Item, item_id)
    # Un oggetto privato altrui risulta inesistente, così non se ne rivela nemmeno la presenza.
    if item is None or not (item.is_public or item.created_by_id == user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Oggetto non trovato")
    return item


def _save(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(422, "Stanza o categoria inesistente")


@app.get("/items", response_model=list[ItemOut])
def list_items(
    q: str | None = None,
    room_id: int | None = None,
    category_id: int | None = None,
    to_find: bool | None = None,
    limit: int = Query(500, ge=1, le=1000),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    query = select(Item).where(_visible_to(user))
    for word in (q or "").split():
        pattern = f"%{word}%"
        query = query.where(or_(*(column.ilike(pattern) for column in SEARCH_COLUMNS)))
    if room_id is not None:
        query = query.where(Item.room_id == room_id)
    if category_id is not None:
        query = query.where(Item.category_id == category_id)
    if to_find is not None:
        query = query.where(Item.to_find == to_find)
    return db.scalars(query.order_by(func.lower(Item.name)).limit(limit)).all()


@app.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = Item(**data.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(item)
    _save(db)
    db.refresh(item)
    return item


@app.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, data: ItemIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = _get_item(item_id, db, user)
    if data.is_public != item.is_public and item.created_by_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo chi ha aggiunto l'oggetto può cambiarne la visibilità")
    for field, value in data.model_dump().items():
        setattr(item, field, value)
    item.updated_by_id = user.id
    item.updated_at = func.now()
    _save(db)
    db.refresh(item)
    return item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    db.delete(_get_item(item_id, db, user))
    db.commit()
