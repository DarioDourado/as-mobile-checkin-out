# SOLID Principles — FastAPI

## Objectivos
Garantir que a arquitectura FastAPI se mantém limpa, escalável, testável e fácil de manter através da aplicação rigorosa dos princípios SOLID nas camadas Routers → Services → Repositories.

---

## 1. Single Responsibility Principle (SRP)
> *Um módulo deve ter apenas uma razão para mudar.*

- **Routers:** Apenas lidam com HTTP (request/response, status codes, dependencies).
- **Services:** Contêm exclusivamente lógica de negócio.
- **Repositories:** Lidam exclusivamente com a base de dados.
- **Schemas:** Apenas validação e transformação de dados (Pydantic).

```python
# ❌ Errado — Router com lógica de negócio e acesso directo à DB
@router.post("/users")
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar():
        raise HTTPException(400, "Email já existe")
    hashed = bcrypt.hash(data.password)
    user = User(email=data.email, password_hash=hashed)
    db.add(user)
    await db.commit()
    return user

# ✅ Correcto — Router apenas delega
@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return await service.create(data)

# Service trata a lógica de negócio
class UserService:
    async def create(self, data: UserCreate) -> UserResponse:
        if await self.repo.email_exists(data.email):
            raise HTTPException(400, "Email já existe")
        hashed = bcrypt.hash(data.password)
        user = await self.repo.create(email=data.email, password_hash=hashed)
        return UserResponse.model_validate(user)

# Repository trata apenas a DB
class UserRepository:
    async def email_exists(self, email: str) -> bool:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar() is not None
```

---

## 2. Open-Closed Principle (OCP)
> *Aberto para extensão, fechado para modificação.*

Adicionar comportamento via composição e injecção — sem alterar código existente.

```python
# ❌ Errado — Service modificado a cada novo canal de notificação
class UserService:
    async def create(self, data: UserCreate):
        user = await self.repo.create(data)
        if settings.NOTIFY_EMAIL:
            await send_email(user.email, "Bem-vindo!")
        if settings.NOTIFY_SMS:
            await send_sms(user.phone, "Bem-vindo!")
        return user

# ✅ Correcto — Protocol define contrato, Service recebe implementações
from typing import Protocol

class NotificationService(Protocol):
    async def send_welcome(self, user: User) -> None: ...

class EmailNotification:
    async def send_welcome(self, user: User) -> None:
        await send_email(user.email, "Bem-vindo!")

class SMSNotification:
    async def send_welcome(self, user: User) -> None:
        await send_sms(user.phone, "Bem-vindo!")

class UserService:
    def __init__(self, repo: UserRepository, notifiers: list[NotificationService]):
        self.repo = repo
        self.notifiers = notifiers

    async def create(self, data: UserCreate) -> User:
        user = await self.repo.create(data)
        for notifier in self.notifiers:
            await notifier.send_welcome(user)
        return user
```

---

## 3. Liskov Substitution Principle (LSP)
> *Subtipos devem poder substituir os seus tipos base sem quebrar o comportamento.*

```python
# ❌ Errado — SubRepository quebra o contrato (lança excepção inesperada)
class BaseRepository:
    async def get_by_id(self, id: str) -> User | None: ...  # retorna None se não encontrado

class CachedUserRepository(BaseRepository):
    async def get_by_id(self, id: str) -> User | None:
        result = await self.cache.get(id)
        if not result:
            raise CacheMissError("Not in cache")  # ❌ quebra o contrato — devia retornar None

# ✅ Correcto — fallback transparente, mesmo contrato
class CachedUserRepository(BaseRepository):
    async def get_by_id(self, id: str) -> User | None:
        cached = await self.cache.get(f"user:{id}")
        if cached:
            return User.model_validate_json(cached)
        user = await super().get_by_id(id)
        if user:
            await self.cache.set(f"user:{id}", user.model_dump_json())
        return user
```

---

## 4. Interface Segregation Principle (ISP)
> *Interfaces específicas são melhores que uma interface geral.*

```python
# ❌ Errado — Protocol monolítico força métodos desnecessários
class IUserRepository(Protocol):
    async def get_by_id(self, id: str) -> User | None: ...
    async def create(self, data: UserCreate) -> User: ...
    async def bulk_import(self, users: list[UserCreate]) -> int: ...
    # AuthService só precisa de get_by_email — não devia implementar bulk_import

# ✅ Correcto — Protocols segregados por responsabilidade
class UserReader(Protocol):
    async def get_by_id(self, id: str) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...

class UserWriter(Protocol):
    async def create(self, data: UserCreate) -> User: ...
    async def update(self, id: str, data: UserUpdate) -> User: ...

class UserBulkOps(Protocol):
    async def bulk_import(self, users: list[UserCreate]) -> int: ...

# AuthService depende apenas do que precisa
class AuthService:
    def __init__(self, user_reader: UserReader):
        self.user_reader = user_reader
```

---

## 5. Dependency Inversion Principle (DIP)
> *Módulos de alto nível não devem depender de módulos de baixo nível. Ambos devem depender de abstrações.*

```python
# ❌ Errado — Service instancia dependências directamente
class UserService:
    def __init__(self):
        self.repo = UserRepository(db=get_sync_db())   # acoplamento directo
        self.mailer = SMTPMailer(host=settings.SMTP_HOST)

# ✅ Correcto — dependências injectadas via Depends()
class UserService:
    def __init__(self, repo: UserRepository, mailer: NotificationService):
        self.repo = repo
        self.mailer = mailer

async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(
        repo=UserRepository(db),
        mailer=EmailNotification(settings.SMTP_HOST),
    )

@router.get("/users/{id}", response_model=UserResponse)
async def get_user(
    id: str,
    service: UserService = Depends(get_user_service),
):
    return await service.get_by_id(id)

# Teste — mock injectado sem alterar código de produção
async def test_get_user():
    mock_service = AsyncMock(spec=UserService)
    mock_service.get_by_id.return_value = UserResponse(id="1", email="test@test.com")
    app.dependency_overrides[get_user_service] = lambda: mock_service
    response = await client.get("/users/1")
    assert response.status_code == 200
```

---

## Checklist SOLID

```
□ Routers sem lógica de negócio (apenas Depends + return service.method())
□ Services sem queries SQLAlchemy directas (apenas chamadas a Repository)
□ Repositories sem lógica de negócio (apenas queries + mapeamento para schema)
□ Dependências injectadas via Depends(), nunca instanciadas dentro da classe
□ Protocols definidos para contratos entre camadas
□ Testes usam dependency_overrides para substituir dependências reais
```
