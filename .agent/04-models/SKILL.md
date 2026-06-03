# MODELS - SQLAlchemy Async

## Base Model

```python
# app/models/base.py
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase
from ulid import ULID


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def generate_ulid() -> str:
    return str(ULID())
```

## User Model

```python
# app/models/user.py
from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_ulid


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(26), primary_key=True, default=generate_ulid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum("admin", "user", name="user_role"), default="user")

    # Relações
    posts = relationship("Post", back_populates="author")

    def __repr__(self):
        return f"<User {self.email}>"
```

## Relações

```python
# app/models/post.py
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, generate_ulid


class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id = Column(String(26), primary_key=True, default=generate_ulid)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    author_id = Column(String(26), ForeignKey("users.id", ondelete="CASCADE"))

    author = relationship("User", back_populates="posts")
```

## Database Connection (Async)

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings

# SQLite async
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace(
    "sqlite://", "sqlite+aiosqlite://"
)

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

## Dependency: get_db

```python
# app/dependencies/database.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## Queries Async

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Select all
async def get_all(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()

# Select one
async def get_by_id(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# Insert
async def create(db: AsyncSession, user: User):
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
```

## Regras

| Regra                   | Descrição              |
| ----------------------- | ---------------------- |
| ULID para IDs           | Não auto-increment     |
| TimestampMixin          | created_at, updated_at |
| Async engine            | `create_async_engine`  |
| `aiosqlite` para SQLite | Driver async           |
| `ondelete="CASCADE"`    | Para FKs               |
