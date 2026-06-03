# FastAPI Enterprise (Modular)

Sistema de prompts modular para desenvolvimento **FastAPI** como backend API para aplicações React/React Native, optimizado para **Machine Learning** e grandes volumes de dados.

## 📦 Instalação

```bash
mkdir -p .agent/skills
cp -r /caminho/para/fastapi-enterprise-modular .agent/skills/fastapi-enterprise
```

## 🗂 Índice de Módulos

### 🏗 Core

- **[00-meta](./00-meta/SKILL.md)** — Visão geral e filosofia
- **[01-architecture](./01-architecture/SKILL.md)** — Async, Services, Repositories
- **[02-folder-structure](./02-folder-structure/SKILL.md)** — Estrutura de pastas

### 🔌 API

- **[03-routes](./03-routes/SKILL.md)** — APIRouter
- **[04-models](./04-models/SKILL.md)** — SQLAlchemy Async
- **[05-schemas](./05-schemas/SKILL.md)** — Pydantic DTOs

### 🗄 Database

- **[06-migrations](./06-migrations/SKILL.md)** — Alembic
- **[07-seeding](./07-seeding/SKILL.md)** — Faker

### 🔐 Auth & Infra

- **[08-auth](./08-auth/SKILL.md)** — JWT httpOnly Cookies
- **[10-docker](./10-docker/SKILL.md)** — Containers
- **[11-env](./11-env/SKILL.md)** — Pydantic Settings
- **[12-cors](./12-cors/SKILL.md)** — Cross-Origin Resource Sharing
- **[13-repositories](./13-repositories/SKILL.md)** — Abstração de Queries
- **[14-rules](./14-rules/SKILL.md)** — Do's and Don'ts
- **[15-websockets](./15-websockets/SKILL.md)** — Native WebSockets Realtime
- **[16-solid](./16-solid/SKILL.md)** — Princípios SOLID Aplicados
- **[17-security](./17-security/SKILL.md)** — Auditor de Segurança Preventivo

### 🤖 Machine Learning

- **[09-ml-integration](./09-ml-integration/SKILL.md)** — Model loading, inference (joblib + hash verification)

### 🧪 Qualidade & Observabilidade

- **[18-testing](./18-testing/SKILL.md)** — pytest-asyncio, conftest, factories, coverage
- **[19-logging](./19-logging/SKILL.md)** — structlog, JSON logs, request_id middleware
- **[20-rate-limiting](./20-rate-limiting/SKILL.md)** — slowapi, brute force protection
- **[21-observability](./21-observability/SKILL.md)** — Prometheus metrics, OpenTelemetry tracing
- **[22-cicd](./22-cicd/SKILL.md)** — GitHub Actions CI/CD pipeline
- **[23-cache](./23-cache/SKILL.md)** — Redis cache, session store, ML inference cache
- **[24-api-versioning](./24-api-versioning/SKILL.md)** — /api/v1/ prefix, multi-version strategy
- **[25-code-review](./25-code-review/SKILL.md)** — Auditor de arquitectura, convenções e padrões (FastAPIReviewAgent)

---

## 🚀 Stack

| Tech                 | Versão | Propósito              |
| -------------------- | ------ | ---------------------- |
| FastAPI              | 0.100+ | Framework              |
| Python               | 3.11+  | Linguagem              |
| SQLAlchemy           | 2.0+   | ORM async              |
| Pydantic             | 2.0+   | Validação              |
| Alembic              | Latest | Migrations             |
| Docker               | Latest | Containers             |
| Redis                | 7+     | Cache + Rate limiting  |
| structlog            | Latest | Logging estruturado    |
| slowapi              | Latest | Rate limiting          |
| prometheus-fastapi-instrumentator | Latest | Métricas |
| opentelemetry-sdk    | Latest | Distributed tracing    |
| pytest-asyncio       | Latest | Testes async           |

## 🗄 Database Strategy

- **Dev:** SQLite (`sqlite:///./sqlite.db`)
- **Prod:** MySQL via Docker

---

## 🔗 Agente Complementar — React Enterprise

Este agente cobre o **backend FastAPI**. Para o frontend React que consome esta API, existe um agente complementar:

**[react-enterprise-modular](../react-enterprise-modular/)** — arquitectura React, auth (token em memória + httpOnly cookie), React Query, WebSockets, segurança frontend, CI/CD, performance.

Os dois agentes foram desenhados para funcionar em conjunto:

| FastAPI Agent | React Agent |
|---|---|
| 08-auth — JWT + httpOnly cookies | 08-auth — token em memória + interceptors Axios |
| 15-websockets — auth por primeiro frame | 18-websockets — `getToken()` + auth por primeiro frame |
| 17-security — OWASP backend | 17-security — XSS, tokens, RBAC frontend |
| 22-cicd — GitHub Actions (Python) | 26-ci-quality — GitHub Actions (Node/TypeScript) |
