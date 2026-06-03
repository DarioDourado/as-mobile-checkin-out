# FASTAPI ENTERPRISE MASTER v1.0

> **Tipo:** Prompt Consolidado  
> **Stack:** FastAPI + Python 3.11+ + SQLAlchemy  
> **Para módulos detalhados:** `fastapi-enterprise-modular/`

---

## ARQUITECTURA: ASYNC-FIRST

```
┌─────────────────────────────────────────────────────┐
│                    FASTAPI APP                       │
├─────────────────────────────────────────────────────┤
│  Routers → Services → Repositories → Models        │
├─────────────────────────────────────────────────────┤
│              SQLAlchemy ORM (async)                  │
├─────────────────────────────────────────────────────┤
│                    Database                          │
└─────────────────────────────────────────────────────┘
```

| Camada           | Responsabilidade              |
| ---------------- | ----------------------------- |
| **Routers**      | Endpoints, validação Pydantic |
| **Services**     | Lógica de negócio             |
| **Repositories** | Queries async                 |
| **Models**       | SQLAlchemy tables             |
| **Schemas**      | Pydantic DTOs                 |

---

## ESTRUTURA

```
app/
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   └── users.py
├── services/
│   └── user_service.py
├── repositories/
│   └── user_repository.py
├── models/
│   └── user.py
├── schemas/
│   └── user.py
├── db/
│   ├── database.py
│   └── session.py
├── dependencies/
│   └── auth.py
├── config/
│   └── settings.py
├── main.py
│
alembic/
└── versions/
```

---

## STACK

| Lib             | Propósito     |
| --------------- | ------------- |
| FastAPI         | Framework     |
| Python 3.11+    | Language      |
| SQLAlchemy 2+   | ORM (async)   |
| Pydantic v2     | Validação     |
| Alembic         | Migrations    |
| python-jose     | JWT           |
| passlib[bcrypt] | Password hash |
| uvicorn         | Server        |

---

## ROUTER

```python
# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserResponse])
async def get_users(service: UserService = Depends()):
    return await service.get_all()

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, service: UserService = Depends()):
    return await service.create(data)
```

---

## SERVICE

```python
# app/services/user_service.py
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

class UserService:
    def __init__(self, repository: UserRepository = Depends()):
        self.repository = repository

    async def get_all(self):
        return await self.repository.find_all()

    async def create(self, data: UserCreate):
        hashed = pwd_context.hash(data.password)
        return await self.repository.create({
            **data.model_dump(exclude={"password"}),
            "password_hash": hashed,
        })
```

---

## REPOSITORY

```python
# app/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.db.session import get_db

class UserRepository:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def find_all(self) -> list[User]:
        result = await self.db.execute(select(User))
        return result.scalars().all()

    async def create(self, data: dict) -> User:
        user = User(**data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
```

---

## SCHEMAS (Pydantic)

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

    class Config:
        from_attributes = True
```

---

## AUTH (JWT httpOnly Cookies)

```python
# app/routers/auth.py
from fastapi import Response
from jose import jwt

@router.post("/login")
async def login(data: LoginRequest, response: Response):
    user = await authenticate(data.email, data.password)

    token = jwt.encode({"sub": user.id}, SECRET_KEY, algorithm="HS256")

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,  # HTTPS
        samesite="strict",
        max_age=3600,
    )

    return {"user": user}
```

---

## ML INTEGRATION

```python
# app/ml/predictor.py
import pickle
from pathlib import Path

class Predictor:
    def __init__(self):
        model_path = Path("models/model.pkl")
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

    def predict(self, features: list[float]) -> float:
        return self.model.predict([features])[0]

# Router
@router.post("/predict")
async def predict(data: PredictRequest, predictor: Predictor = Depends()):
    return {"prediction": predictor.predict(data.features)}
```

---

## DATABASE STRATEGY

| Ambiente | Database       |
| -------- | -------------- |
| Dev      | SQLite (async) |
| Prod     | MySQL          |

```bash
# Migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## REGRAS ABSOLUTAS

### ✅ SEMPRE

- `async/await` para I/O
- Pydantic para validação
- Dependency Injection
- Repositories para queries
- Services para lógica
- Type hints em tudo
- JWT httpOnly cookies
- Respeitar os princípios SOLID (SRP, OCP, LSP, ISP, DIP)
- Auditoria de Segurança contínua ("Security by Design")

### ❌ NUNCA

- Sync I/O em async context
- Lógica em routers
- Queries em routers
- Hardcoded secrets
- `print()` em produção

---

## CHECKLIST NOVO DOMÍNIO

```
□ app/models/{domain}.py
□ app/schemas/{domain}.py
□ app/repositories/{domain}_repository.py
□ app/services/{domain}_service.py
□ app/routers/{domain}.py
□ alembic revision (migration)
□ app/main.py (include router)
```
