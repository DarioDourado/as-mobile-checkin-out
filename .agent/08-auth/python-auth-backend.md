# python-auth-backend.md
# Módulo Python (FastAPI) de Autenticação — Reutilizável para múltiplos projetos

## Stack

- **FastAPI** — framework web
- **SQLAlchemy 2.0** — ORM (async)
- **python-jose** — JWT (HS256)
- **passlib[bcrypt]** — hashing de passwords
- **fastapi-mail** — envio de e-mails
- **alembic** — migrações de BD

```bash
pip install fastapi uvicorn sqlalchemy asyncpg python-jose[cryptography] passlib[bcrypt] fastapi-mail python-dotenv alembic
```

---

## Estrutura de ficheiros

```
app/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── auth/
│   ├── __init__.py
│   ├── router.py       ← endpoints /auth/*
│   ├── service.py      ← lógica de negócio
│   ├── jwt.py          ← geração/validação de tokens
│   ├── dependencies.py ← get_current_user (middleware)
│   └── mailer.py       ← envio de e-mails
└── .env
```

---

## .env

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
JWT_SECRET=muda_isto_para_algo_muito_secreto_32chars_min
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
APP_URL=https://tua-app.com
MAIL_USERNAME=noreply@tua-app.com
MAIL_PASSWORD=password
MAIL_FROM=noreply@tua-app.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

---

## database.py

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_async_engine(os.getenv("DATABASE_URL"), echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

---

## models.py

```python
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

class PasswordReset(Base):
    __tablename__ = "password_resets"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
```

---

## schemas.py

```python
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class ForgotRequest(BaseModel):
    email: EmailStr

class ResetRequest(BaseModel):
    token: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class MessageResponse(BaseModel):
    message: str
```

---

## auth/jwt.py

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

load_dotenv()

SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))


def create_access_token(data: dict) -> str:
    payload = {**data, "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE)}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    payload = {**data, "type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE)}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    except JWTError:
        return None
```

---

## auth/mailer.py

```python
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from dotenv import load_dotenv
import os

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

mailer = FastMail(conf)


async def send_email(to: str, subject: str, body: str):
    msg = MessageSchema(subject=subject, recipients=[to], body=body, subtype=MessageType.plain)
    await mailer.send_message(msg)
```

---

## auth/service.py

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets
import os

from models import User, RefreshToken, PasswordReset
from schemas import LoginRequest, RegisterRequest, ForgotRequest, ResetRequest
from auth.jwt import create_access_token, create_refresh_token, decode_token
from auth.mailer import send_email

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
APP_URL = os.getenv("APP_URL", "http://localhost:3000")


def _hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()


# ── Login ──────────────────────────────────────────────────────────────────────

async def login(data: LoginRequest, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not pwd_ctx.verify(data.password, user.password_hash):
        raise ValueError("Credenciais inválidas.")

    if not user.is_verified:
        raise PermissionError("Conta não verificada. Verifica o teu e-mail.")

    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=_hash(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    ))
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "email": user.email},
    }


# ── Register ───────────────────────────────────────────────────────────────────

async def register(data: RegisterRequest, db: AsyncSession) -> dict:
    if len(data.password) < 8:
        raise ValueError("A palavra-passe deve ter pelo menos 8 caracteres.")

    exists = await db.execute(select(User).where(User.email == data.email))
    if exists.scalar_one_or_none():
        raise ValueError("E-mail já registado.")

    token = secrets.token_hex(32)
    user = User(
        name=data.name,
        email=data.email,
        password_hash=pwd_ctx.hash(data.password),
        verification_token=token,
    )
    db.add(user)
    await db.commit()

    verify_url = f"{APP_URL}/auth/verify?token={token}"
    await send_email(data.email, "Verifica a tua conta", f"Clica aqui para verificar:\n{verify_url}")

    return {"message": "Conta criada. Verifica o teu e-mail."}


# ── Verify Email ───────────────────────────────────────────────────────────────

async def verify_email(token: str, db: AsyncSession) -> dict:
    result = await db.execute(
        select(User).where(User.verification_token == token, User.is_verified == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Token inválido ou já utilizado.")

    user.is_verified = True
    user.verification_token = None
    await db.commit()

    return {"message": "Conta verificada com sucesso."}


# ── Forgot Password ────────────────────────────────────────────────────────────

async def forgot_password(data: ForgotRequest, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Resposta sempre igual — não revelar se o e-mail existe
    if not user:
        return {"message": "Se o e-mail existir, receberás um link em breve."}

    token = secrets.token_hex(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)

    await db.execute(delete(PasswordReset).where(PasswordReset.user_id == user.id))
    db.add(PasswordReset(user_id=user.id, token=token, expires_at=expires))
    await db.commit()

    reset_url = f"{APP_URL}/auth/reset?token={token}"
    await send_email(data.email, "Recuperação de palavra-passe", f"Clica aqui para redefinir:\n{reset_url}")

    return {"message": "Se o e-mail existir, receberás um link em breve."}


# ── Reset Password ─────────────────────────────────────────────────────────────

async def reset_password(data: ResetRequest, db: AsyncSession) -> dict:
    if len(data.password) < 8:
        raise ValueError("A palavra-passe deve ter pelo menos 8 caracteres.")

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(PasswordReset).where(PasswordReset.token == data.token, PasswordReset.expires_at > now)
    )
    reset = result.scalar_one_or_none()
    if not reset:
        raise ValueError("Token inválido ou expirado.")

    user_result = await db.execute(select(User).where(User.id == reset.user_id))
    user = user_result.scalar_one()
    user.password_hash = pwd_ctx.hash(data.password)

    await db.execute(delete(PasswordReset).where(PasswordReset.token == data.token))
    await db.commit()

    return {"message": "Palavra-passe atualizada com sucesso."}


# ── Refresh Token ──────────────────────────────────────────────────────────────

async def refresh_token(token: str, db: AsyncSession) -> dict:
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise ValueError("Token inválido.")

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == _hash(token),
            RefreshToken.expires_at > now,
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise ValueError("Token revogado ou expirado.")

    access_token = create_access_token({"sub": payload["sub"]})
    return {"access_token": access_token, "token_type": "bearer"}


# ── Logout ─────────────────────────────────────────────────────────────────────

async def logout(token: str, db: AsyncSession) -> dict:
    await db.execute(delete(RefreshToken).where(RefreshToken.token_hash == _hash(token)))
    await db.commit()
    return {"message": "Sessão terminada."}
```

---

## auth/dependencies.py

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User
from auth.jwt import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") == "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")

    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilizador não encontrado.")

    return user
```

---

## auth/router.py

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import LoginRequest, RegisterRequest, ForgotRequest, ResetRequest, RefreshRequest
from auth import service

router = APIRouter(prefix="/auth", tags=["auth"])


def http_error(e: Exception) -> HTTPException:
    code = status.HTTP_401_UNAUTHORIZED if isinstance(e, PermissionError) else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(e))


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await service.login(data, db)
    except (ValueError, PermissionError) as e:
        raise http_error(e)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await service.register(data, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/verify")
async def verify(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        return await service.verify_email(token, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forgot")
async def forgot(data: ForgotRequest, db: AsyncSession = Depends(get_db)):
    return await service.forgot_password(data, db)


@router.post("/reset")
async def reset(data: ResetRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await service.reset_password(data, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh")
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await service.refresh_token(data.refresh_token, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await service.logout(data.refresh_token, db)
```

---

## main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth.router import router as auth_router

app = FastAPI(title="Auth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://tua-app.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


# Exemplo de rota protegida:
# from auth.dependencies import get_current_user
# @app.get("/me")
# async def me(user = Depends(get_current_user)):
#     return {"id": user.id, "name": user.name, "email": user.email}
```

---

## Arrancar o servidor

```bash
# Desenvolvimento
uvicorn main:app --reload --port 8000

# Produção (com gunicorn)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Docs automáticas disponíveis em `http://localhost:8000/docs`
