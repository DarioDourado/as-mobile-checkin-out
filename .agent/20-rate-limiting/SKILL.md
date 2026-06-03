# RATE LIMITING - Protecção Brute Force

## Stack

| Lib             | Propósito                                      |
| --------------- | ---------------------------------------------- |
| **slowapi**     | Rate limiting para FastAPI (baseado em limits) |
| **redis**       | Backend para contadores distribuídos           |

## Instalação

```bash
pip install slowapi redis
```

## Configuração Global

```python
# app/config/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],   # limite global por IP
    storage_uri="redis://redis:6379" # Redis em produção
)
```

## Registar no Main

```python
# app/main.py
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config.limiter import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

## Aplicar por Endpoint

```python
# app/routers/auth.py
from fastapi import APIRouter, Request
from app.config.limiter import limiter

router = APIRouter()


@router.post("/login")
@limiter.limit("5/minute")          # 5 tentativas por minuto por IP
async def login(request: Request, credentials: LoginRequest, ...):
    ...


@router.post("/register")
@limiter.limit("3/hour")            # 3 registos por hora por IP
async def register(request: Request, data: UserCreate, ...):
    ...


@router.post("/refresh")
@limiter.limit("20/minute")
async def refresh(request: Request, ...):
    ...
```

## Limite por User Autenticado

```python
# Usar user_id como chave em vez de IP (mais preciso)
def get_user_id(request: Request) -> str:
    """Extrai user_id do cookie/token para usar como chave de rate limit."""
    from app.utils.security import decode_token
    token = request.cookies.get("access_token")
    if token:
        payload = decode_token(token)
        if payload:
            return payload.get("sub", get_remote_address(request))
    return get_remote_address(request)


user_limiter = Limiter(
    key_func=get_user_id,
    storage_uri="redis://redis:6379"
)


@router.post("/export")
@user_limiter.limit("10/hour")      # 10 exports por hora por user
async def export_data(request: Request, ...):
    ...
```

## Resposta ao Cliente

Quando o limite é atingido, a API retorna automaticamente:

```
HTTP 429 Too Many Requests
Retry-After: 60
Content-Type: application/json

{"error": "Rate limit exceeded: 5 per 1 minute"}
```

## Dev: In-Memory (sem Redis)

```python
# app/config/limiter.py
from app.config.settings import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri=settings.REDIS_URL if settings.PRODUCTION else "memory://"
)
```

## Settings

```python
# app/config/settings.py (adicionar)
REDIS_URL: str = "redis://redis:6379"
```

## Regras

| Endpoint         | Limite recomendado | Motivo                    |
| ---------------- | ------------------ | ------------------------- |
| `POST /login`    | 5/minute           | Brute force de passwords  |
| `POST /register` | 3/hour             | Account farming           |
| `POST /refresh`  | 20/minute          | Token refresh flood       |
| `POST /ml/*`     | 10/minute          | Inference é CPU-intensivo |
| `GET /`          | 200/minute         | Consultas normais         |
