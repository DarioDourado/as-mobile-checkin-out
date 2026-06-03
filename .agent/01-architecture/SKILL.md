# ARCHITECTURE - Arquitectura FastAPI

## Paradigma: Async API + ML Ready

```
┌─────────────────────────────────────────────────────┐
│            FRONTEND (React/React Native)            │
│  - Cookies httpOnly (JWT)                           │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP + Cookie
                      ▼
┌─────────────────────────────────────────────────────┐
│                   FASTAPI                            │
├─────────────────────────────────────────────────────┤
│  Routers → Dependencies → Services → Repositories   │
├─────────────────────────────────────────────────────┤
│            SQLAlchemy Async Models                   │
├─────────────────────────────────────────────────────┤
│                   MySQL/SQLite                       │
├─────────────────────────────────────────────────────┤
│            ML Models (opcional)                      │
└─────────────────────────────────────────────────────┘
```

## Camadas

| Camada           | Responsabilidade        | Localização         |
| ---------------- | ----------------------- | ------------------- |
| **Routers**      | Definir endpoints       | `app/routers/`      |
| **Dependencies** | Injecção, Auth          | `app/dependencies/` |
| **Schemas**      | Pydantic DTOs           | `app/schemas/`      |
| **Services**     | Lógica de negócio       | `app/services/`     |
| **Repositories** | Abstracção queries      | `app/repositories/` |
| **Models**       | SQLAlchemy ORM          | `app/models/`       |
| **ML**           | Model loading/inference | `app/ml/`           |

## Fluxo de Request

```
Request → Router → Dependency (auth/db)
                         ↓
                    Schema (validação Pydantic)
                         ↓
                    Service (lógica)
                         ↓
              Repository (queries async)
                         ↓
                    Model (SQLAlchemy)
                         ↓
                Schema (response Pydantic)
                         ↓
                    Response
```

## Async: Porquê?

```python
# Síncrono (bloqueia)
def get_users():
    return db.query(User).all()  # Bloqueia thread

# Assíncrono (não bloqueia)
async def get_users():
    result = await db.execute(select(User))  # Não bloqueia
    return result.scalars().all()
```

| Cenário                  | Sync ou Async?     |
| ------------------------ | ------------------ |
| Database queries         | Async ✅           |
| HTTP requests externos   | Async ✅           |
| ML inference (CPU-bound) | Sync no threadpool |
| File I/O                 | Async ✅           |

## Dependency Injection

```python
from fastapi import Depends
from app.dependencies import get_db, get_current_user

@router.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ...
```

## Regras

| Regra                     | Descrição                |
| ------------------------- | ------------------------ |
| Async por defeito         | Todas as funções I/O     |
| Pydantic para validação   | Não validar manualmente  |
| Dependencies para DI      | get_db, get_current_user |
| Services para lógica      | Negócio fora do router   |
| Repositories para queries | Queries fora do Service  |
