# SCHEMAS - Pydantic DTOs

## Porquê Schemas?

| Propósito               | Pydantic Schema |
| ----------------------- | --------------- |
| Validação de input      | ✅              |
| Serialização de output  | ✅              |
| Documentação automática | ✅ (OpenAPI)    |
| Type safety             | ✅              |

## Base Config

```python
# app/schemas/base.py
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

## User Schemas

```python
# app/schemas/user.py
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.schemas.base import BaseSchema


# Request: Create
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)


# Request: Update
class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    email: EmailStr | None = None


# Response
class UserResponse(BaseSchema):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime


# Response com relações
class UserWithPostsResponse(UserResponse):
    posts: list["PostResponse"] = []
```

## Auth Schemas

```python
# app/schemas/auth.py
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: int
    type: str  # access | refresh
```

## Validação Customizada

```python
from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    name: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase")
        return v
```

## Uso nos Routers

```python
from app.schemas.user import UserCreate, UserResponse

@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate):  # Validado automaticamente
    ...
```

## Conversão Model ↔ Schema

```python
# Model → Schema (response)
user_model = await service.get_by_id(user_id)
return UserResponse.model_validate(user_model)

# Schema → Model (create)
user_dict = user_data.model_dump()
user = User(**user_dict)
```

## Regras

| Regra                    | Descrição              |
| ------------------------ | ---------------------- | ------------------- |
| `from_attributes=True`   | Para converter de ORM  |
| Request vs Response      | Schemas separados      |
| `Field()` para validação | min_length, max_length |
| `EmailStr` para emails   | Validação automática   |
| Optional com `           | None`                  | Python 3.10+ syntax |
