# OBSERVABILITY - Métricas + Tracing

## Stack

| Lib                             | Propósito                          |
| ------------------------------- | ---------------------------------- |
| **prometheus-fastapi-instrumentator** | Métricas HTTP automáticas    |
| **opentelemetry-sdk**           | Distributed tracing                |
| **opentelemetry-instrumentation-fastapi** | Auto-instrumentação FastAPI|
| **opentelemetry-exporter-otlp** | Exportar traces (Jaeger, Grafana)  |

## Instalação

```bash
pip install prometheus-fastapi-instrumentator \
            opentelemetry-sdk \
            opentelemetry-instrumentation-fastapi \
            opentelemetry-exporter-otlp-proto-grpc
```

## Métricas Prometheus

```python
# app/config/metrics.py
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,       # ENABLE_METRICS=true
    should_instrument_requests_inprogress=True,
    inprogress_labels=True,
)
```

```python
# app/main.py
from app.config.metrics import instrumentator

# Registar métricas — expõe /metrics
instrumentator.instrument(app).expose(app, include_in_schema=False)
```

Aceder em: `GET /metrics` — formato Prometheus scrape.

## Métricas Custom (ML)

```python
# app/config/metrics.py (adicionar)
from prometheus_client import Counter, Histogram

ml_predictions_total = Counter(
    "ml_predictions_total",
    "Total de predições ML",
    ["model", "result"]
)

ml_prediction_duration = Histogram(
    "ml_prediction_duration_seconds",
    "Duração das predições ML",
    ["model"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)
```

```python
# app/ml/inference.py
import time
from app.config.metrics import ml_predictions_total, ml_prediction_duration

def predict_classification(self, features: list[float]) -> dict:
    with ml_prediction_duration.labels(model="classifier").time():
        model = self.registry.load("classifier")
        prediction = model.predict([features])[0]

    ml_predictions_total.labels(model="classifier", result=str(prediction)).inc()
    return {"prediction": int(prediction)}
```

## Tracing com OpenTelemetry

```python
# app/config/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


def setup_tracing(app, otlp_endpoint: str = "http://jaeger:4317") -> None:
    provider = TracerProvider()
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
```

```python
# app/main.py
from app.config.tracing import setup_tracing
from app.config.settings import settings

if settings.TRACING_ENABLED:
    setup_tracing(app, otlp_endpoint=settings.OTLP_ENDPOINT)
```

## Span Manual (para lógica crítica)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


async def create_user(self, data: UserCreate) -> User:
    with tracer.start_as_current_span("user.create") as span:
        span.set_attribute("user.email", data.email)
        user = await self.repo.create(data)
        span.set_attribute("user.id", user.id)
        return user
```

## Docker Compose (Observability Stack)

```yaml
# docker-compose.observability.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"   # UI
      - "4317:4317"     # OTLP gRPC
```

## prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "fastapi"
    static_configs:
      - targets: ["api:8000"]
    metrics_path: /metrics
```

## Settings

```python
# app/config/settings.py (adicionar)
TRACING_ENABLED: bool = False
OTLP_ENDPOINT: str = "http://jaeger:4317"
```

## Métricas HTTP Disponíveis (automáticas)

| Métrica                             | Tipo      | Descrição                   |
| ----------------------------------- | --------- | --------------------------- |
| `http_requests_total`               | Counter   | Total de requests por rota  |
| `http_request_duration_seconds`     | Histogram | Latência por rota           |
| `http_requests_inprogress`          | Gauge     | Requests activos            |
| `ml_predictions_total`              | Counter   | Predições por modelo        |
| `ml_prediction_duration_seconds`    | Histogram | Latência de inferência ML   |
