# CACHE - Redis

## Stack

| Lib              | Propósito                              |
| ---------------- | -------------------------------------- |
| **redis[asyncio]** | Cliente async Redis                  |
| **fastapi-cache2** | Cache decorator para endpoints       |

## Instalação

```bash
pip install "redis[asyncio]" fastapi-cache2
```

## Configuração

```python
# app/config/redis.py
from redis.asyncio import Redis, ConnectionPool
from app.config.settings import settings

_pool: ConnectionPool | None = None


def get_redis_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,
            decode_responses=True,
        )
    return _pool


async def get_redis() -> Redis:
    return Redis(connection_pool=get_redis_pool())
```

## Inicializar no Main (fastapi-cache2)

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from app.config.redis import get_redis


@asynccontextmanager
async def lifespan(app):
    redis = await get_redis()
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield
    await redis.aclose()
```

## Cache em Endpoints (decorator)

```python
# app/routers/users.py
from fastapi_cache.decorator import cache


@router.get("/", response_model=list[UserResponse])
@cache(expire=60)   # TTL em segundos
async def get_users(service: UserService = Depends()):
    return await service.get_all()


@router.get("/{user_id}", response_model=UserResponse)
@cache(expire=300)  # 5 minutos
async def get_user(user_id: str, service: UserService = Depends()):
    return await service.get_by_id(user_id)
```

## Invalidar Cache (após mutações)

```python
# app/services/user_service.py
from fastapi_cache import FastAPICache


class UserService:
    async def create(self, data: UserCreate) -> User:
        user = await self.repo.create(data)
        await FastAPICache.clear(namespace="fastapi-cache")  # invalida tudo
        return user

    async def update(self, user_id: str, data: UserUpdate) -> User:
        user = await self.repo.update(user_id, data)
        # Invalidar chave específica
        backend = FastAPICache.get_backend()
        await backend.clear(key=f"fastapi-cache:GET:/api/v1/users/{user_id}")
        return user
```

## Cache Manual (para lógica de negócio)

```python
# app/services/user_service.py
import json
from app.config.redis import get_redis


class UserService:
    async def get_by_id(self, user_id: str) -> User:
        redis = await get_redis()
        cache_key = f"user:{user_id}"

        # Tentar cache primeiro
        cached = await redis.get(cache_key)
        if cached:
            return User(**json.loads(cached))

        # Miss: ir à DB
        user = await self.repo.get_by_id(user_id)
        if user:
            await redis.setex(
                cache_key,
                300,  # TTL 5 minutos
                json.dumps({"id": user.id, "email": user.email, "name": user.name})
            )
        return user
```

## Cache de Resultados ML

```python
# app/ml/inference.py
import hashlib
import json
from app.config.redis import get_redis


class PredictionService:
    async def predict_cached(self, model_name: str, features: list[float]) -> dict:
        redis = await get_redis()
        cache_key = f"ml:{model_name}:{hashlib.md5(str(features).encode()).hexdigest()}"

        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        result = self.predict_classification(features)
        await redis.setex(cache_key, 3600, json.dumps(result))  # 1 hora
        return result
```

## Session Store (alternativa a cookies para refresh tokens)

```python
# app/services/auth_service.py
async def store_refresh_token(self, user_id: str, token: str) -> None:
    redis = await get_redis()
    await redis.setex(
        f"refresh:{token}",
        7 * 24 * 3600,  # 7 dias
        user_id
    )


async def validate_refresh_token(self, token: str) -> str | None:
    redis = await get_redis()
    return await redis.get(f"refresh:{token}")


async def revoke_refresh_token(self, token: str) -> None:
    redis = await get_redis()
    await redis.delete(f"refresh:{token}")
```

## Docker Compose

```yaml
# docker-compose.yml (adicionar)
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

volumes:
  redis_data:
```

## Settings

```python
# app/config/settings.py (adicionar)
REDIS_URL: str = "redis://redis:6379"
```

## Estratégia de TTL

| Dados                   | TTL sugerido | Motivo                         |
| ----------------------- | ------------ | ------------------------------ |
| Lista de utilizadores   | 60s          | Muda com frequência            |
| Perfil de utilizador    | 300s         | Relativamente estável          |
| Predições ML            | 3600s        | Determinístico, CPU-intensivo  |
| Refresh tokens          | 7 dias       | Igual à validade do token      |
| Sessões                 | 15min        | Igual ao access token          |
