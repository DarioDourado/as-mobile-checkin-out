# SEEDING - Faker + Fixtures

## Estrutura

```
app/
├── seeders/
│   ├── __init__.py
│   ├── base.py
│   ├── user_seeder.py
│   └── run.py           # Entry point
```

## Base Seeder

```python
# app/seeders/base.py
from sqlalchemy.ext.asyncio import AsyncSession


class BaseSeeder:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self):
        raise NotImplementedError
```

## User Seeder

```python
# app/seeders/user_seeder.py
from faker import Faker
from app.seeders.base import BaseSeeder
from app.models.user import User
from app.utils.security import hash_password

fake = Faker()


class UserSeeder(BaseSeeder):
    async def run(self):
        # Admin fixo
        admin = User(
            name="Admin",
            email="admin@example.com",
            password=hash_password("password123"),
            role="admin"
        )
        self.db.add(admin)

        # Users aleatórios
        for _ in range(20):
            user = User(
                name=fake.name(),
                email=fake.unique.email(),
                password=hash_password("password123"),
                role="user"
            )
            self.db.add(user)

        await self.db.commit()
        print("✅ Seeded 21 users")
```

## Run Script

```python
# app/seeders/run.py
import asyncio
from app.database import AsyncSessionLocal
from app.seeders.user_seeder import UserSeeder
from app.seeders.post_seeder import PostSeeder


async def seed():
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding database...")

        # Ordem importa para FKs
        await UserSeeder(db).run()
        await PostSeeder(db).run()

        print("🎉 Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
```

## Executar

```bash
python -m app.seeders.run
```

Ou via script:

```json
// pyproject.toml
[tool.scripts]
seed = "python -m app.seeders.run"
```

## Factory Pattern (Alternativo)

```python
# app/seeders/factories.py
from faker import Faker
from app.models.user import User

fake = Faker()


def create_user(**overrides) -> User:
    return User(
        name=overrides.get("name", fake.name()),
        email=overrides.get("email", fake.unique.email()),
        password=overrides.get("password", "hashed_password"),
        role=overrides.get("role", "user"),
    )


def create_users(count: int) -> list[User]:
    return [create_user() for _ in range(count)]
```

## Regras

| Regra            | Descrição                  |
| ---------------- | -------------------------- |
| Faker para dados | Não inventar               |
| Admin fixo       | Para testes de login       |
| Ordem de seeders | Respeitar FKs              |
| Async seeders    | Usar `await`               |
| `fake.unique`    | Para campos únicos (email) |
