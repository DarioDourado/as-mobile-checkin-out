# AUTH - JWT httpOnly Cookies

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                 FRONTEND (React)                     │
│  - NÃO armazena tokens                              │
│  - Cookies enviados automaticamente                 │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP + Cookie (httpOnly)
                      ▼
┌─────────────────────────────────────────────────────┐
│                   FASTAPI                            │
│  - Access Token: Cookie httpOnly (15min)            │
│  - Refresh Token: Cookie httpOnly (7 dias)          │
└─────────────────────────────────────────────────────┘
```

## Security Utils

```python
# app/utils/security.py
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: str, token_type: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": token_type
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None
```

## Auth Router

```python
# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from app.dependencies.database import get_db
from app.schemas.auth import LoginRequest
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.config import settings

router = APIRouter()


@router.post("/login")
async def login(
    response: Response,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    result = await service.authenticate(credentials.email, credentials.password)

    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        max_age=15 * 60,  # 15 min
        httponly=True,
        secure=settings.PRODUCTION,
        samesite="strict"
    )
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        max_age=7 * 24 * 60 * 60,  # 7 dias
        httponly=True,
        secure=settings.PRODUCTION,
        samesite="strict"
    )

    return {"user": UserResponse.model_validate(result["user"])}


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    service = AuthService(db)
    result = await service.refresh(refresh_token)

    if not result:
        raise HTTPException(status_code=401, detail="Invalid token")

    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        max_age=15 * 60,
        httponly=True,
        secure=settings.PRODUCTION,
        samesite="strict"
    )

    return {"user": UserResponse.model_validate(result["user"])}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}
```

## Dependency: get_current_user

```python
# app/dependencies/auth.py
from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.utils.security import decode_token
from app.models.user import User
from sqlalchemy import select


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
```

## Proteger Rotas: Router-Level Dependencies

> **Nunca usar middleware para auth.** O middleware não tem acesso às dependências do router e obriga a manter uma allowlist de rotas públicas — frágil e fácil de esquecer.
>
> A abordagem correcta é **dois APIRouters separados**: um público, um protegido.

### Padrão: Public vs Protected Routers

```python
# app/api/v1/router.py
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.api.v1 import auth, users, products, health

# ── Rotas PÚBLICAS — sem autenticação ──────────────────────────
public_router = APIRouter(prefix="/api/v1")

public_router.include_router(auth.router,   prefix="/auth",   tags=["Auth"])
public_router.include_router(health.router, prefix="/health", tags=["Health"])

# ── Rotas PROTEGIDAS — JWT obrigatório em TODAS ────────────────
protected_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(get_current_user)],  # aplicado a todos os endpoints abaixo
)

protected_router.include_router(users.router,    prefix="/users",    tags=["Users"])
protected_router.include_router(products.router, prefix="/products", tags=["Products"])
```

```python
# app/main.py
from app.api.v1.router import public_router, protected_router

app.include_router(public_router)
app.include_router(protected_router)
```

**Resultado:** qualquer endpoint registado em `protected_router` retorna `401` automaticamente se o cookie `access_token` estiver ausente ou inválido — sem uma única linha extra nos handlers.

---

### Aceder ao User no Handler

O `get_current_user` já corre como dependência do router, mas para aceder ao objecto `User` dentro do handler basta redeclará-lo como parâmetro:

```python
# app/api/v1/users.py
from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    # get_current_user NÃO corre duas vezes — FastAPI usa cache por request
    return current_user


@router.get("/", response_model=list[UserResponse])
async def list_users(
    service: UserService = Depends(),
    current_user: User = Depends(get_current_user),  # acesso ao user autenticado
):
    return await service.get_all()
```

> FastAPI resolve cada dependência **uma vez por request** e faz cache — declarar `Depends(get_current_user)` no router E no handler não causa double-query à DB.

---

### Rota "Soft Auth" (opcional)

Para rotas que funcionam com ou sem autenticação (ex: conteúdo público com dados extra para logados):

```python
# app/dependencies/auth.py
async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None  # não rejeita — retorna None

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    return result.scalar_one_or_none()
```

```python
@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    current_user: User | None = Depends(get_optional_user),
):
    if current_user:
        return await feed_service.get_personalized(current_user.id)
    return await feed_service.get_public()
```

---

### Protecção por Role (RBAC)

```python
# app/dependencies/auth.py
from enum import StrEnum

class Role(StrEnum):
    ADMIN = "admin"
    USER  = "user"


def require_role(*roles: Role):
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return dependency
```

```python
# Apenas admins
@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    ...

# Admin ou moderador
@router.post("/{id}/feature")
async def feature_post(
    current_user: User = Depends(require_role(Role.ADMIN, Role.MODERATOR)),
):
    ...
```

---

### Resumo da Arquitectura

```
app/api/v1/router.py
│
├── public_router  (prefix=/api/v1)
│   ├── POST /auth/login        ← sem auth
│   ├── POST /auth/logout       ← sem auth
│   ├── POST /auth/refresh      ← sem auth
│   └── GET  /health            ← sem auth
│
└── protected_router  (prefix=/api/v1, Depends(get_current_user))
    ├── GET  /users/            ← 401 se sem JWT
    ├── GET  /users/me          ← 401 se sem JWT
    ├── POST /products/         ← 401 se sem JWT
    └── ...
```

---

## Regras

| Regra                                              | Descrição                                 |
| -------------------------------------------------- | ----------------------------------------- |
| httpOnly SEMPRE                                    | Nunca expor token ao JS                   |
| samesite: strict                                   | Protecção CSRF                            |
| secure em prod                                     | Apenas HTTPS                              |
| Access Token curto                                 | 15 minutos                                |
| Refresh Token longo                                | 7 dias                                    |
| bcrypt para passwords                              | Nunca plain text                          |
| Router-level deps para auth                        | Nunca middleware com allowlist            |
| `Depends()` cache por request                      | Sem double-query à DB                     |
| `get_optional_user` para rotas soft-auth           | Não rejeita anónimos, enriquece se logado |

## Implementação de Referência

O ficheiro [`python-auth-backend.md`](./python-auth-backend.md) nesta pasta contém uma implementação completa e reutilizável do sistema de auth: modelos SQLAlchemy, schemas Pydantic, JWT service, mailer, dependencies e router. Usar como ponto de partida para novos projectos.
