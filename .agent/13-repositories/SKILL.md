# REPOSITORIES - Abstração de Queries

## Propósito

Isolar queries do database dos Services para:

- Queries reutilizáveis
- Testes mais fáceis (mock)
- Separação de responsabilidades

## Estrutura

```
app/
└── repositories/
    ├── __init__.py
    ├── base.py           # Repository genérico
    ├── user_repository.py
    └── {domain}_repository.py
```

## Base Repository

```python
# app/repositories/base.py
from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def find_all(self) -> List[ModelType]:
        result = await self.db.execute(select(self.model))
        return result.scalars().all()

    async def find_by_id(self, id: str) -> Optional[ModelType]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> ModelType:
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: str, data: dict) -> Optional[ModelType]:
        instance = await self.find_by_id(id)
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
            await self.db.commit()
            await self.db.refresh(instance)
        return instance

    async def delete(self, id: str) -> bool:
        instance = await self.find_by_id(id)
        if instance:
            await self.db.delete(instance)
            await self.db.commit()
            return True
        return False
```

## Repository Específico

```python
# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models.user import User
from fastapi import Depends
from app.db.session import get_db

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession = Depends(get_db)):
        super().__init__(User, db)

    async def find_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def find_active(self) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.is_active == True)
        )
        return result.scalars().all()
```

## Uso em Service

```python
# app/services/user_service.py
from app.repositories.user_repository import UserRepository
from fastapi import Depends

class UserService:
    def __init__(self, repository: UserRepository = Depends()):
        self.repository = repository

    async def get_all(self):
        return await self.repository.find_all()

    async def get_by_email(self, email: str):
        return await self.repository.find_by_email(email)
```

## Regras

| Regra               | Descrição                |
| ------------------- | ------------------------ |
| Base genérico       | CRUD reutilizável        |
| Depends()           | Injecção automática      |
| Queries específicas | No repository do domínio |
| Services usam Repos | Nunca db directo         |
