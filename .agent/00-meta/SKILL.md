# META - FastAPI Enterprise

> **Sistema:** FastAPI Enterprise  
> **Versão:** 1.1  
> **Ambiente:** Docker

## Sobre

Sistema de prompts modular para desenvolvimento **FastAPI** como backend API para aplicações React/React Native, optimizado para **Machine Learning** e grandes volumes de dados.

## Stack

| Tecnologia | Versão | Propósito         |
| ---------- | ------ | ----------------- |
| FastAPI    | 0.100+ | Framework         |
| Python     | 3.11+  | Linguagem         |
| SQLAlchemy | 2.0+   | ORM               |
| Pydantic   | 2.0+   | Validação/Schemas |
| Alembic    | Latest | Migrations        |
| Docker     | Latest | Containers        |

## Estrutura de Módulos

```
fastapi-enterprise-modular/
├── 00-meta/           → Este ficheiro
├── 01-architecture/   → Async, Services, Repositories
├── 02-folder-structure/ → Estrutura de pastas
├── 03-routes/         → APIRouter, endpoints
├── 04-models/         → SQLAlchemy async
├── 05-schemas/        → Pydantic DTOs (Request/Response)
├── 06-migrations/     → Alembic
├── 07-seeding/        → Faker + fixtures
├── 08-auth/           → JWT httpOnly cookies + RBAC
├── 09-ml-integration/ → Model serving (joblib, ThreadPool)
├── 10-docker/         → Containers (dev + prod)
├── 11-env/            → Pydantic Settings
├── 12-cors/           → CORS config
├── 13-repositories/   → Abstracção de queries SQLAlchemy
├── 14-rules/          → ⚠️  Lei Absoluta — consultar sempre
├── 15-websockets/     → WebSockets com auth por primeiro frame
├── 16-solid/          → Princípios SOLID aplicados ao FastAPI
├── 17-security/       → Auditor de segurança (OWASP, CVSS, PoC)
├── 18-testing/        → pytest-asyncio, factories, coverage
├── 19-logging/        → structlog, JSON logs, request_id
├── 20-rate-limiting/  → slowapi, brute force protection
├── 21-observability/  → Prometheus + OpenTelemetry
├── 22-cicd/           → GitHub Actions CI/CD
├── 23-cache/          → Redis cache + session store
├── 24-api-versioning/ → /api/v1/ prefix, multi-version
└── 25-code-review/    → FastAPIReviewAgent (conformidade + arquitectura)
```

## Segurança — dois módulos complementares

| Módulo | Scope |
|--------|-------|
| **17-security** | Auditoria OWASP — XSS, SSRF, IDOR, injecção, CVSS, PoC |
| **25-code-review** | Conformidade com padrões deste sistema — arquitectura, convenções, repositories |

Usar **ambos** em reviews pré-deploy.

## Versioning

A versão do sistema está registada apenas aqui (`00-meta`). Os módulos individuais não têm versão própria. Ao actualizar um módulo, actualiza também a versão do sistema neste ficheiro.

## Filosofia

1. **Async-First** — Todas as operações I/O assíncronas
2. **Type-Safe** — Pydantic + Type hints em todo o código
3. **ML Ready** — Estrutura para carregar e servir modelos
4. **SQLite Dev → MySQL Prod** — Migrations portáveis via Alembic
5. **Docker Native** — Ambiente reproduzível
6. **Observable** — Logs estruturados, métricas Prometheus, tracing OpenTelemetry

## Stack Completa

| Tecnologia | Versão | Propósito |
|---|---|---|
| FastAPI | 0.100+ | Framework |
| Python | 3.11+ | Linguagem |
| SQLAlchemy | 2.0+ | ORM async |
| Pydantic | 2.0+ | Validação/Schemas |
| Alembic | Latest | Migrations |
| Docker | Latest | Containers |
| Redis | 7+ | Cache + Rate limiting |
| structlog | Latest | Logging estruturado |
| slowapi | Latest | Rate limiting |
| prometheus-fastapi-instrumentator | Latest | Métricas |
| opentelemetry-sdk | Latest | Distributed tracing |
| pytest-asyncio | Latest | Testes async |
