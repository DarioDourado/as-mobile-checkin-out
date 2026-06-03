# RULES - Regras Absolutas FastAPI

## ✅ SEMPRE

| #   | Regra                                  |
| --- | -------------------------------------- |
| 1   | `async def` para endpoints             |
| 2   | Pydantic schemas para validação        |
| 3   | `response_model` em todos os endpoints |
| 4   | Dependencies para injecção (db, auth)  |
| 5   | Services para lógica de negócio        |
| 6   | Repositories para queries              |
| 7   | Type hints em todo o código            |
| 8   | Alembic para migrations                |
| 9   | Docker para ambiente                   |
| 10  | ULID para IDs                          |
| 11  | structured logging com `structlog` + `request_id` em cada log ([19-logging](../19-logging/SKILL.md)) |
| 12  | Rate limiting em endpoints públicos e de auth ([20-rate-limiting](../20-rate-limiting/SKILL.md)) |
| 13  | Mensagens de commit em Conventional Commits (feat/fix/docs/refactor/test/chore) |
| 14  | PR deve passar todos os checks de CI antes de merge ([22-cicd](../22-cicd/SKILL.md)) |
| 15  | Auth em WebSockets via primeiro frame `{"type": "auth", "token": "..."}` — nunca em query param ([15-websockets](../15-websockets/SKILL.md)) |

## ❌ NUNCA

| #   | Regra                         |
| --- | ----------------------------- |
| 1   | Sync I/O em async functions   |
| 2   | Retornar Models directamente  |
| 3   | Lógica de negócio nos routers |
| 4   | Queries fora de repositories  |
| 5   | Secrets hardcoded             |
| 6   | Auto-increment IDs            |
| 7   | Commitar `.env`               |
| 8   | `*` em CORS origins (prod)                              |
| 9   | Token em query param em WebSockets (`?token=...`)       |
| 10  | `print()` em produção — usar `structlog.get_logger()`   |
| 11  | `# noqa` sem comentário explicativo (ex: `# noqa: E501 — URL longa gerada`)  |
| 12  | Merge de PR com checks de CI a falhar                   |
| 13  | `pickle.load()` directamente em modelos ML — usar joblib + hash SHA-256 |

## Checklist: Novo Endpoint

```
□ Schema de Request (Pydantic)
□ Schema de Response (Pydantic)
□ Router com async def
□ response_model definido
□ Dependencies (db, auth)
□ Service method
□ Repository method (se query)
□ Testes
```

## Checklist: Novo Model

```
□ SQLAlchemy model em app/models/
□ Importar em models/__init__.py
□ Alembic migration
□ alembic upgrade head
□ Seeder atualizado
□ Schemas Request/Response
```

## Checklist: Deploy

```
□ docker-compose.prod.yml configurado
□ DATABASE_URL=mysql+aiomysql://...
□ SECRET_KEY gerado
□ PRODUCTION=true
□ CORS_ORIGINS correcto
□ alembic upgrade head executado
□ --workers em prod (4+)
```

## Checklist: Pre-deploy

```
□ CI passa (lint + mypy + bandit + pip-audit + tests + coverage)
□ alembic upgrade head executado
□ Secrets via env (não hardcoded)
□ CORS_ORIGINS sem wildcard
□ Rate limiting activo nos endpoints públicos
□ Logs estruturados (structlog) — sem print()
□ Conventional Commits em todos os commits do PR
□ Code review com 25-code-review + 17-security feito
```

## Checklist: ML Model

```
□ Modelo treinado em app/ml/models/
□ Loader atualizado
□ Pre-load no lifespan startup
□ Inference service method
□ Schema para features
□ Router endpoint
□ ThreadPool se CPU-bound
```
