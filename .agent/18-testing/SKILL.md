# TESTING - pytest + pytest-asyncio

## Stack

| Lib                  | Propósito                        |
| -------------------- | -------------------------------- |
| **pytest**           | Framework de testes              |
| **pytest-asyncio**   | Suporte async/await              |
| **httpx**            | Client HTTP async para testes    |
| **factory-boy**      | Factories para dados de teste    |
| **pytest-cov**       | Coverage report                  |

## Estrutura

```
tests/
├── conftest.py            # Fixtures globais (DB, client, auth)
├── factories.py           # factory-boy factories
├── unit/
│   ├── test_user_service.py
│   └── test_security.py
└── integration/
    ├── test_auth.py
    └── test_users.py
```

## conftest.py

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.base import Base
from app.dependencies.database import get_db

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine_test, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """Client já autenticado com cookies de sessão."""
    await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    return client
```

## factories.py

```python
# tests/factories.py
import factory
from app.models.user import User
from app.utils.security import hash_password


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(lambda: __import__("ulid").new().str)
    name = factory.Faker("name")
    email = factory.Faker("email")
    hashed_password = factory.LazyFunction(lambda: hash_password("TestPass123!"))
    is_active = True
```

## Teste de Integração

```python
# tests/integration/test_auth.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(auth_client: AsyncClient):
    response = await auth_client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert "access_token" not in response.cookies
```

## Teste Unitário de Service

```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from tests.factories import UserFactory


@pytest.mark.asyncio
async def test_create_user():
    mock_repo = AsyncMock()
    mock_user = UserFactory.build()
    mock_repo.create.return_value = mock_user

    service = UserService(repository=mock_repo)
    result = await service.create(UserCreate(
        name="Test User",
        email="test@example.com",
        password="TestPass123!"
    ))

    assert result.email == mock_user.email
    mock_repo.create.assert_called_once()
```

## pytest.ini / pyproject.toml

Configurar thresholds de coverage no `pyproject.toml` — o CI falha automaticamente se não forem atingidos (ver [22-cicd](../22-cicd/SKILL.md)).

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
filterwarnings = ["ignore::DeprecationWarning"]

[tool.coverage.run]
source = ["app"]
omit = [
    "app/migrations/*",
    "app/seeding/*",
    "**/__init__.py",
]

[tool.coverage.report]
fail_under = 70        # CI falha se coverage < 70%
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

**Prioridade de coverage por camada:**

| Camada | Prioridade | Motivo |
|--------|-----------|--------|
| Services | Alta | Lógica de negócio centralizada |
| Repositories | Alta | Queries críticas |
| Routes | Média | Integração — cobrir fluxos principais |
| ML inference | Alta | Erros silenciosos custam caro |

## Executar Testes

```bash
# Todos os testes
pytest

# Com coverage (falha se < 70%)
pytest --cov=app --cov-report=html --cov-fail-under=70

# Só integração
pytest tests/integration/

# Verbose
pytest -v

# Só unit tests (rápido)
pytest tests/unit/ -v
```

## Regras

| Regra                                   | Motivo                                |
| --------------------------------------- | ------------------------------------- |
| DB em memória (SQLite) para testes      | Isolamento, velocidade                |
| `rollback` após cada teste              | Evita estado partilhado entre testes  |
| `dependency_overrides` para injectar DB | Não alterar código de produção        |
| Factories para dados de teste           | DRY, dados realistas                  |
| Mocks nos unit tests                    | Testar apenas a camada alvo           |
| Coverage threshold ≥ 70%               | Definido em pyproject.toml + CI falha se não atingido |
