# ENV - Configuração

## Pydantic Settings

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "FastAPI Enterprise"
    PRODUCTION: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./sqlite.db"

    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

## .env.example

```bash
# App
APP_NAME=FastAPI Enterprise
PRODUCTION=false

# Database (dev = SQLite)
DATABASE_URL=sqlite:///./sqlite.db

# Database (prod = MySQL)
# DATABASE_URL=mysql+aiomysql://user:pass@host:3306/dbname

# Auth
SECRET_KEY=your-super-secret-key-here

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

## Uso

```python
from app.config import settings

# Acesso directo
db_url = settings.DATABASE_URL
is_prod = settings.PRODUCTION

# Ou via dependency
from fastapi import Depends
from app.config import get_settings, Settings

@router.get("/info")
async def info(settings: Settings = Depends(get_settings)):
    return {"app": settings.APP_NAME}
```

## CORS Setup

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # Para cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## SQLite → MySQL

```bash
# .env (dev)
DATABASE_URL=sqlite:///./sqlite.db

# .env (prod)
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/myapp
```

## Gerar Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Regras

| Regra                    | Descrição           |
| ------------------------ | ------------------- |
| Pydantic Settings        | Type-safe config    |
| @lru_cache               | Singleton           |
| .env não commitada       | Apenas .env.example |
| CORS_ORIGINS como list   | Múltiplas origens   |
| `allow_credentials=True` | Para cookies        |
