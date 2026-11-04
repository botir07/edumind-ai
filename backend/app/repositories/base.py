"""Generic CRUD repository base with multi-tenant organization scoping."""
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    def _has_column(self, name: str) -> bool:
        return hasattr(self.model.__table__.c, name)

    async def get(self, id: Any) -> Optional[ModelType]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        organization_id: Optional[Any] = None,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
    ):
        query = select(self.model)
        if organization_id is not None and self._has_column("organization_id"):
            query = query.where(self.model.organization_id == organization_id)  # type: ignore[attr-defined]
        if filters:
            for key, value in filters.items():
                if hasattr(self.model.__table__.c, key) and value is not None:
                    query = query.where(getattr(self.model.__table__.c, key) == value)
        if order_by and hasattr(self.model.__table__.c, order_by):
            query = query.order_by(getattr(self.model.__table__.c, order_by))
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self, *, organization_id: Optional[Any] = None, filters: Optional[dict] = None) -> int:
        query = select(func.count()).select_from(self.model)
        if organization_id is not None and self._has_column("organization_id"):
            query = query.where(self.model.organization_id == organization_id)  # type: ignore[attr-defined]
        if filters:
            for key, value in filters.items():
                if hasattr(self.model.__table__.c, key) and value is not None:
                    query = query.where(getattr(self.model.__table__.c, key) == value)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, obj_in: CreateSchemaType, **extra) -> ModelType:
        data = obj_in.model_dump(exclude_unset=True)
        data.update(extra)
        obj = self.model(**data)  # type: ignore[call-arg]
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: Any, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        obj = await self.get(id)
        if not obj:
            return None
        data = obj_in.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(obj, key, value)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: Any) -> bool:
        obj = await self.get(id)
        if not obj:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        return True
