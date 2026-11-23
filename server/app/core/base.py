from typing import Generic, TypeVar
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError

T = TypeVar("T")


def new_id() -> str:
    return uuid4().hex


class BaseRepository(Generic[T]):
    """Data access only. No business rules, no authorization."""

    model: type[T]

    def __init__(self, session: Session):
        self.session = session

    def get(self, id_: str) -> T | None:
        return self.session.get(self.model, id_)

    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity


class BaseService(Generic[T]):
    """Single-entity business logic. Talks only to its own repository."""

    entity_name = "Resource"

    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository

    def get_or_raise(self, id_: str) -> T:
        entity = self.repository.get(id_)
        if entity is None:
            raise NotFoundError(f"{self.entity_name} '{id_}' not found")
        return entity
