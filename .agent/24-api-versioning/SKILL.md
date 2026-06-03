# API VERSIONING - /api/v1/

## Estratégia

Versionar via prefixo de URL: `/api/v1/`, `/api/v2/`. Cada versão é um `APIRouter` independente.

## Estrutura

```
app/
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py       # Agrega todos os routers v1
│   │   ├── auth.py
│   │   └── users.py
│   └── v2/                 # Versão futura
│       ├── __init__.py
│       └── router.py
└── main.py
```

## v1/router.py

```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1 import auth, users

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router,  prefix="/auth",  tags=["Auth v1"])
router.include_router(users.router, prefix="/users", tags=["Users v1"])
```

## Registar no Main

```python
# app/main.py
from app.api.v1.router import router as v1_router

app.include_router(v1_router)
```

## Endpoints resultantes

```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/users/
POST   /api/v1/users/
GET    /api/v1/users/{id}
PUT    /api/v1/users/{id}
DELETE /api/v1/users/{id}
```

## Migrar para v2 (exemplo)

```python
# app/api/v2/users.py — apenas os endpoints que mudaram
from fastapi import APIRouter
from app.api.v1.users import router as v1_router  # herdar v1
from app.schemas.user_v2 import UserResponseV2     # novo schema

router = APIRouter()

# Sobrescrever apenas o endpoint que mudou
@router.get("/{user_id}", response_model=UserResponseV2)
async def get_user_v2(user_id: str, ...):
    ...
```

```python
# app/api/v2/router.py
from fastapi import APIRouter
from app.api.v1 import auth           # reutilizar v1 sem alterações
from app.api.v2 import users          # versão nova

router = APIRouter(prefix="/api/v2")

router.include_router(auth.router,  prefix="/auth",  tags=["Auth v2"])
router.include_router(users.router, prefix="/users", tags=["Users v2"])
```

## Deprecation Header

```python
# app/api/v1/router.py — sinalizar v1 como deprecated quando v2 existir
from fastapi import APIRouter, Response
from starlette.middleware.base import BaseHTTPMiddleware


class DeprecationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/v1/"):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "Sat, 01 Jan 2028 00:00:00 GMT"
            response.headers["Link"] = '</api/v2/>; rel="successor-version"'
        return response
```

## Health Check (sem versão)

```python
# app/main.py — endpoint sem prefixo de versão
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "version": "1.0.0"}
```

## OpenAPI por versão

```python
# app/main.py — documentação separada por versão (opcional)
app = FastAPI(
    title="API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)
```

## Regras

| Regra                                         | Motivo                                  |
| --------------------------------------------- | --------------------------------------- |
| Nunca alterar schema existente de uma versão  | Quebra clientes em produção             |
| Manter v1 activa pelo menos 6 meses após v2   | Dar tempo de migração                   |
| Usar `Deprecation` + `Sunset` headers         | Comunicar fim de vida da versão         |
| `/health` e `/metrics` sem prefixo de versão  | Infra não deve depender de versão de API|
| Herdar routers de v1 em v2 quando possível    | Evitar duplicação de código             |
