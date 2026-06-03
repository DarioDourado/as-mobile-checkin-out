# FOLDER STRUCTURE - Estrutura de Pastas FastAPI

## Árvore Base

```
app/
├── main.py                    # Entry point
├── config.py                  # Settings (Pydantic)
├── database.py                # DB connection
│
├── routers/                   # API Routes
│   ├── __init__.py
│   ├── auth.py
│   └── users.py
│
├── models/                    # SQLAlchemy Models
│   ├── __init__.py
│   ├── base.py               # Base model
│   └── user.py
│
├── schemas/                   # Pydantic Schemas
│   ├── __init__.py
│   ├── user.py
│   └── auth.py
│
├── services/                  # Business Logic
│   ├── __init__.py
│   ├── auth_service.py
│   └── user_service.py
│
├── repositories/              # Query Abstraction
│   ├── __init__.py
│   └── user_repository.py
│
├── dependencies/              # Dependency Injection
│   ├── __init__.py
│   ├── database.py           # get_db
│   └── auth.py               # get_current_user
│
├── ml/                        # Machine Learning
│   ├── __init__.py
│   ├── models/               # Trained models (.pkl, .onnx)
│   └── inference.py          # Model loading & prediction
│
└── utils/                     # Helpers
    └── security.py

alembic/                       # Migrations
├── versions/
└── env.py

tests/
├── conftest.py
└── test_users.py

.env
.env.example
Dockerfile
docker-compose.yml
requirements.txt
alembic.ini
```

## Convenções de Nomenclatura

| Tipo       | Padrão                     | Exemplo              |
| ---------- | -------------------------- | -------------------- |
| Router     | `{plural}.py`              | `users.py`           |
| Model      | `{singular}.py`            | `user.py`            |
| Schema     | `{singular}.py`            | `user.py`            |
| Service    | `{singular}_service.py`    | `user_service.py`    |
| Repository | `{singular}_repository.py` | `user_repository.py` |

## Imports

```python
# Router
from app.routers import auth, users

# Model
from app.models.user import User

# Schema
from app.schemas.user import UserCreate, UserResponse

# Service
from app.services.user_service import UserService

# Repository
from app.repositories.user_repository import UserRepository
```

## main.py Exemplo

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users
from app.config import settings

app = FastAPI(title=settings.APP_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
```

## Regras

| Regra                            | Descrição                |
| -------------------------------- | ------------------------ |
| Ficheiros lowercase              | `user.py`, não `User.py` |
| `__init__.py` em todas as pastas | Package structure        |
| Schemas separados                | Request e Response       |
| ML isolado                       | Pasta `ml/` dedicada     |
