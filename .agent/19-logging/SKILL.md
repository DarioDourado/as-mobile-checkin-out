# LOGGING - Structured Logging

## Stack

| Lib                    | Propósito                          |
| ---------------------- | ---------------------------------- |
| **structlog**          | Logging estruturado (JSON/console) |
| **python-json-logger** | Alternativa mais leve              |

## Configuração (structlog)

```python
# app/config/logging.py
import logging
import sys
import structlog


def setup_logging(json_logs: bool = False, log_level: str = "INFO") -> None:
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    if json_logs:
        # Produção: JSON lines — compatível com Datadog, CloudWatch, Loki
        renderer = structlog.processors.JSONRenderer()
    else:
        # Dev: output colorido e legível
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())
```

## Inicializar no Main

```python
# app/main.py
from app.config.logging import setup_logging
from app.config.settings import settings

setup_logging(json_logs=settings.PRODUCTION, log_level=settings.LOG_LEVEL)
```

## Uso no Código

```python
# Em qualquer camada (service, repository, router)
import structlog

log = structlog.get_logger(__name__)


class UserService:
    async def create(self, data: UserCreate) -> User:
        log.info("user.create.start", email=data.email)
        try:
            user = await self.repo.create(data)
            log.info("user.create.success", user_id=user.id, email=user.email)
            return user
        except Exception as exc:
            log.error("user.create.failed", email=data.email, error=str(exc))
            raise
```

## Request ID Middleware

```python
# app/middleware/logging.py
import uuid
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        log.info("request.start")
        response = await call_next(request)
        log.info("request.end", status_code=response.status_code)

        response.headers["X-Request-ID"] = request_id
        return response
```

## Registar Middleware no Main

```python
# app/main.py
from app.middleware.logging import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)
```

## Settings

```python
# app/config/settings.py (adicionar)
LOG_LEVEL: str = "INFO"      # DEBUG em dev, INFO em prod
```

## Exemplo de Output JSON (Produção)

```json
{"event": "request.start", "request_id": "a1b2c3", "method": "POST", "path": "/api/v1/users", "level": "info", "timestamp": "2026-05-20T10:00:00Z"}
{"event": "user.create.success", "request_id": "a1b2c3", "user_id": "01HZ...", "email": "user@example.com", "level": "info", "timestamp": "2026-05-20T10:00:00.050Z"}
{"event": "request.end", "request_id": "a1b2c3", "status_code": 201, "level": "info", "timestamp": "2026-05-20T10:00:00.055Z"}
```

## Regras

| Regra                              | Motivo                                |
| ---------------------------------- | ------------------------------------- |
| Nunca `print()` em produção        | Não é persistido nem estruturado      |
| Usar `log.info/warning/error`      | Níveis semânticos para alertas        |
| Incluir sempre `request_id`        | Rastreabilidade de pedidos            |
| JSON em produção                   | Compatível com qualquer log aggregator|
| Nunca logar passwords ou tokens    | Segurança / GDPR                      |
