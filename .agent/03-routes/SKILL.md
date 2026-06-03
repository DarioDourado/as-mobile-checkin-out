# ROUTES - APIRouter

## Estrutura de Router

```python
# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = UserService(db)
    return await service.get_all(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = UserService(db)
    return await service.create(user_data)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = UserService(db)
    user = await service.update(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = UserService(db)
    deleted = await service.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
```

## Registar Routers

```python
# app/main.py
from fastapi import FastAPI
from app.routers import auth, users

app = FastAPI()

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
```

## Path Parameters

```python
@router.get("/{user_id}")
async def get_user(user_id: str):  # Validação automática
    ...

@router.get("/{user_id}/posts/{post_id}")
async def get_user_post(user_id: str, post_id: str):
    ...
```

## Query Parameters

```python
@router.get("/")
async def get_users(
    skip: int = 0,           # Optional com default
    limit: int = 20,
    role: str | None = None  # Optional sem default
):
    ...
```

## Regras

| Regra                     | Descrição                 |
| ------------------------- | ------------------------- |
| `response_model` sempre   | Documenta e valida output |
| `status_code` para create | 201 em POST               |
| Dependencies para DI      | `Depends(get_db)`         |
| HTTPException para erros  | Não retornar dicts        |
| async def                 | Todas as funções          |
