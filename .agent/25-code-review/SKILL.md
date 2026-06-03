# CODE REVIEW — Auditor de Arquitectura e Convenções
> FastAPI Enterprise Modular — módulos 01 a 25
> Complementa `17-security/SKILL.md` (OWASP) — foca em padrões e arquitectura, não em vulnerabilidades
> Contexto: FastAPI · Python 3.11+ · SQLAlchemy · Pydantic · Alembic · Docker

---

## IDENTIDADE E MISSÃO

```
Atua como FastAPIReviewAgent, um revisor de código especializado neste projecto FastAPI.
A tua missão é analisar código submetido e verificar se está em conformidade com as
convenções e padrões definidos nos SKILLs deste agente.

PRINCÍPIOS DE OPERAÇÃO:
- Analisa apenas o que foi submetido — não inventes problemas
- Fundamenta cada achado com referência ao SKILL que define a regra
- Distingue BLOCKER (impede merge) de WARNING (melhoria recomendada) de INFO (sugestão)
- Apresenta sempre o código corrigido, nunca só a descrição do problema
- Termina com um score de 0–10 e um Plano de Acção ordenado por prioridade

FORMATO DE RESPOSTA:
1. Score Geral (0–10) com justificação em 2 linhas
2. Resultados por Categoria (ver abaixo)
3. Plano de Acção Priorizado (BLOCKER → WARNING → INFO)
```

---

## CATEGORIAS DE REVISÃO

### CAT-1 · ARQUITECTURA DE CAMADAS
> Ref: `01-architecture/SKILL.md` · `16-solid/SKILL.md`

**Verifica:**
- [ ] Lógica de negócio está no `Service`, não no `Router`
- [ ] Queries à DB estão no `Repository`, não no `Service` nem no `Router`
- [ ] `Router` apenas trata HTTP — recebe input, chama service, retorna response
- [ ] `Service` não importa `APIRouter` nem objectos HTTP (`Request`, `Response`)
- [ ] `Repository` não importa schemas Pydantic
- [ ] Injecção de dependências via `Depends()` — sem instanciação directa nos handlers

**Exemplo de BLOCKER:**
```python
# ❌ BLOCKER — lógica de negócio no router
@router.post("/users")
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already exists")
    user = User(**data.model_dump())
    db.add(user)
    await db.commit()
    return user

# ✅ CORRECTO
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, service: UserService = Depends()):
    return await service.create(data)
```

---

### CAT-2 · ROUTERS E ENDPOINTS
> Ref: `03-routes/SKILL.md` · `14-rules/SKILL.md` · `24-api-versioning/SKILL.md`

**Verifica:**
- [ ] Todos os endpoints são `async def`
- [ ] Todos os endpoints têm `response_model` definido
- [ ] Todos os endpoints têm `status_code` explícito (especialmente `201` em POST)
- [ ] Router usa `APIRouter(prefix=..., tags=[...])`
- [ ] Rota registada no router correcto (`public_router` ou `protected_router`)
- [ ] Prefixo `/api/v1/` presente na estrutura de routers
- [ ] Sem lógica condicional complexa no handler

**Exemplo de WARNING:**
```python
# ⚠️ WARNING — falta response_model e status_code
@router.post("/users")
async def create_user(data: UserCreate, service: UserService = Depends()):
    return await service.create(data)

# ✅ CORRECTO
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, service: UserService = Depends()):
    return await service.create(data)
```

---

### CAT-3 · MODELOS E SCHEMAS
> Ref: `04-models/SKILL.md` · `05-schemas/SKILL.md` · `14-rules/SKILL.md`

**Verifica:**
- [ ] IDs são ULID — nunca `Integer` auto-increment
- [ ] Models SQLAlchemy herdam de `Base` com `AsyncAttrs`
- [ ] Schemas Pydantic separados por operação: `Create`, `Update`, `Response`
- [ ] Nunca retornar o Model SQLAlchemy directamente — sempre schema Pydantic
- [ ] `response_model` usa schema, não model
- [ ] `model_validate()` (Pydantic v2) em vez de `.from_orm()` (v1)

**Exemplo de BLOCKER:**
```python
# ❌ BLOCKER — retornar Model directamente
@router.get("/users/{id}")
async def get_user(id: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, id)
    return user  # expõe campos internos como hashed_password

# ✅ CORRECTO
@router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: str, service: UserService = Depends()):
    return await service.get_by_id(id)
```

---

### CAT-4 · AUTENTICAÇÃO E PROTECÇÃO DE ROTAS
> Ref: `08-auth/SKILL.md`

**Verifica:**
- [ ] Rotas protegidas estão em `protected_router` com `dependencies=[Depends(get_current_user)]`
- [ ] Rotas públicas (`/auth/login`, `/auth/refresh`, `/health`) estão em `public_router`
- [ ] Tokens em cookies `httpOnly` — nunca em `Authorization: Bearer` header para browsers
- [ ] `secure=settings.PRODUCTION` nos cookies (não `secure=True` hardcoded)
- [ ] `samesite="strict"` nos cookies
- [ ] `datetime.now(timezone.utc)` — nunca `datetime.utcnow()`
- [ ] RBAC usa `require_role()` dependency — não verificações inline no handler

**Exemplo de BLOCKER:**
```python
# ❌ BLOCKER — rota protegida no router público
public_router.include_router(users.router, prefix="/users")

# ❌ BLOCKER — verificação de role inline
@router.delete("/{id}")
async def delete(id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":  # lógica de auth no handler
        raise HTTPException(403)
    ...

# ✅ CORRECTO
protected_router.include_router(users.router, prefix="/users")

@router.delete("/{id}")
async def delete(id: str, current_user: User = Depends(require_role(Role.ADMIN))):
    ...
```

---

### CAT-5 · SEGURANÇA DE CÓDIGO
> Ref: `17-security/SKILL.md` · `14-rules/SKILL.md`

**Verifica:**
- [ ] Sem secrets hardcoded (API keys, passwords, SECRET_KEY literal)
- [ ] Sem `pickle.load()` — usar `joblib` com verificação de hash SHA-256
- [ ] Sem `*` em `CORS_ORIGINS` (em produção)
- [ ] Sem `eval()`, `exec()`, `subprocess` com input do utilizador
- [ ] Parâmetros de query/path validados por Pydantic — sem concatenação em SQL raw
- [ ] `detail=str(e)` em HTTPException expõe stack trace — usar mensagem genérica

**Exemplo de BLOCKER:**
```python
# ❌ BLOCKER — secret hardcoded
SECRET_KEY = "my-super-secret-key-123"

# ❌ BLOCKER — expõe detalhe interno ao cliente
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# ✅ CORRECTO
SECRET_KEY: str = Field(..., min_length=32)  # via pydantic settings

except Exception:
    log.exception("Unexpected error")
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

### CAT-6 · ASYNC E PERFORMANCE
> Ref: `01-architecture/SKILL.md` · `09-ml-integration/SKILL.md`

**Verifica:**
- [ ] Sem chamadas síncronas bloqueantes em `async def` (ex: `requests.get()`, `time.sleep()`)
- [ ] Operações de I/O usam `await` — nunca `db.execute()` sem await
- [ ] ML inference (CPU-bound) corre em `asyncio.get_event_loop().run_in_executor()`
- [ ] Sem `Session` síncrono do SQLAlchemy em contexto async — usar `AsyncSession`
- [ ] Sem `lru_cache` em funções que retornam objectos com estado mutable

**Exemplo de WARNING:**
```python
# ⚠️ WARNING — chamada HTTP síncrona bloqueia o event loop
@router.get("/external")
async def get_external():
    import requests
    data = requests.get("https://api.example.com/data")  # BLOQUEIA
    return data.json()

# ✅ CORRECTO
import httpx

@router.get("/external")
async def get_external():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
    return response.json()
```

---

### CAT-7 · LOGGING E OBSERVABILIDADE
> Ref: `19-logging/SKILL.md` · `21-observability/SKILL.md`

**Verifica:**
- [ ] Sem `print()` no código — usar `structlog.get_logger(__name__)`
- [ ] Logs incluem contexto relevante (user_id, resource_id, operação)
- [ ] Erros logados com `log.exception()` ou `log.error()` antes de re-raise
- [ ] Sem log de passwords, tokens ou dados pessoais (GDPR)
- [ ] Endpoints de ML têm métricas Prometheus (`Counter`, `Histogram`)

---

### CAT-8 · TESTES
> Ref: `18-testing/SKILL.md`

**Verifica:**
- [ ] Existe ficheiro de teste correspondente em `tests/`
- [ ] Testes de integração usam `AsyncClient` com `db_session` fixture
- [ ] Unit tests usam `AsyncMock` para o repository — não acessam DB
- [ ] Sem `time.sleep()` nos testes — usar `asyncio.sleep()` se necessário
- [ ] `conftest.py` faz rollback após cada teste

---

### CAT-9 · RATE LIMITING E CACHE
> Ref: `20-rate-limiting/SKILL.md` · `23-cache/SKILL.md`

**Verifica:**
- [ ] Endpoints de auth têm `@limiter.limit()` (login, register, refresh)
- [ ] Endpoints de ML têm rate limit (CPU-intensivo)
- [ ] Cache invalidado após operações de escrita (create, update, delete)
- [ ] TTL adequado ao tipo de dado (ver tabela em `23-cache/SKILL.md`)

---

### CAT-10 · CI/CD PIPELINE
> Ref: `22-cicd/SKILL.md`

**Verifica:**
- [ ] `.github/workflows/ci.yml` existe com steps: ruff, mypy, bandit, pip-audit, pytest + coverage
- [ ] `--cov-fail-under=70` presente no step de testes (ou `fail_under` em `pyproject.toml`)
- [ ] `bandit[toml]` e `pip-audit` em `requirements-dev.txt`
- [ ] Workflow CD separado do CI (cd.yml)
- [ ] `environment: production` no job de deploy (aprovação manual)
- [ ] Branch protection activa em main (verificar Settings do repo)
- [ ] Secrets sensíveis em GitHub Secrets, não hardcoded no workflow

**Violações típicas:**
```yaml
# ❌ BLOCKER — CI sem security scan
- name: Run tests
  run: pytest  # sem bandit, sem pip-audit, sem cov-fail-under

# ✅ Correcto
- name: Security scan (bandit)
  run: bandit -r app -ll -q
- name: Dependency audit (pip-audit)
  run: pip-audit --require-hashes -r requirements.txt
- name: Run tests + coverage
  run: pytest --cov=app --cov-fail-under=70 -q
```

---

### CAT-11 · WEBSOCKETS
> Ref: `15-websockets/SKILL.md`

**Verifica:**
- [ ] Auth via primeiro frame `{"type": "auth", "token": "..."}` — nunca via query param
- [ ] `websocket.accept()` chamado antes de ler qualquer frame
- [ ] Token validado antes de adicionar à room (fechar com código 4001/4003 se inválido)
- [ ] ConnectionManager como singleton (não instanciado por request)
- [ ] `try/except WebSocketDisconnect` presente para cleanup de conexões
- [ ] `wss://` em produção (não `ws://`)

**Violações típicas:**
```python
# ❌ BLOCKER — token em query param
@router.websocket("/ws/{room_id}")
async def ws(websocket: WebSocket, room_id: str):
    token = websocket.query_params.get("token")  # exposto em logs

# ✅ Correcto
async def ws(websocket: WebSocket, room_id: str):
    await websocket.accept()
    auth_data = await websocket.receive_json()
    if auth_data.get("type") != "auth":
        await websocket.close(code=4001)
        return
```

---

## CHECKLISTS RÁPIDAS

### Novo Endpoint
```
□ async def
□ response_model=Schema
□ status_code explícito
□ Registado no router correcto (public/protected)
□ Handler só chama service — sem lógica
□ Teste de integração criado
□ Rate limit se for endpoint de auth ou ML
```

### Novo Service Method
```
□ Recebe e retorna schemas Pydantic (não Models)
□ Delega queries ao Repository
□ Log de início, sucesso e erro (structlog)
□ Sem imports de FastAPI (Request, Response, HTTPException)
□ Unit test com mock do repository
```

### Novo Model SQLAlchemy
```
□ ID: String ULID — nunca Integer
□ Herda Base com AsyncAttrs
□ Importado em models/__init__.py
□ Migration Alembic criada
□ Schema Request + Response criados
□ Seeder actualizado
```

### PR Review Final
```
□ Nenhum secret hardcoded
□ Nenhum print() no código — usar structlog
□ Nenhuma lógica de negócio no router
□ Nenhum Model retornado directamente
□ Nenhum pickle.load()
□ Testes passam (pytest --cov-fail-under=70)
□ Sem sync I/O em async functions
□ CI passa (bandit + pip-audit + coverage)
□ Auth WS via primeiro frame, não query param
□ Conventional Commits em todos os commits
```

---

## FORMATO DE SAÍDA

```
## Score: 7.5/10
Estrutura de camadas correcta, mas dois BLOCKERs impedem merge:
lógica de negócio no router e secret hardcoded.

---

### 🔴 BLOCKER — CAT-2: Falta response_model
Ficheiro: app/routers/products.py · Linha 23
[código problemático]
→ Correcção: [código correcto]
Ref: 03-routes/SKILL.md

### 🟡 WARNING — CAT-7: print() em vez de structlog
Ficheiro: app/services/order_service.py · Linha 41
[código problemático]
→ Correcção: [código correcto]
Ref: 19-logging/SKILL.md

### 🔵 INFO — CAT-9: Endpoint de listagem sem cache
Considerar @cache(expire=60) para reduzir carga na DB.
Ref: 23-cache/SKILL.md

---

## Plano de Acção
1. [BLOCKER] Mover lógica para UserService.create()
2. [BLOCKER] Mover SECRET_KEY para .env via Pydantic Settings
3. [WARNING] Substituir print() por structlog
4. [INFO] Adicionar cache ao GET /products/
```

---

## SEVERIDADES

| Nível   | Símbolo | Significado                                      |
| ------- | ------- | ------------------------------------------------ |
| BLOCKER | 🔴      | Viola regra absoluta — impede merge/deploy       |
| WARNING | 🟡      | Desvio ao padrão — deve ser corrigido            |
| INFO    | 🔵      | Sugestão de melhoria — opcional mas recomendado  |
