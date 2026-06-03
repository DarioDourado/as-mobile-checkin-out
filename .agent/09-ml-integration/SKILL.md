# ML INTEGRATION - Model Serving

## Estrutura

```
app/
├── ml/
│   ├── __init__.py
│   ├── models/              # Modelos treinados
│   │   ├── classifier.pkl
│   │   └── regressor.onnx
│   ├── loader.py            # Carregamento de modelos
│   └── inference.py         # Lógica de predição
```

## Model Loader (Singleton)

> ⚠️ **Segurança:** Nunca usar `pickle.load()` directamente — permite execução de código arbitrário (RCE) se o ficheiro for comprometido. Usar `joblib` com verificação de hash SHA-256.

```python
# app/ml/loader.py
import hashlib
import joblib
from pathlib import Path
from functools import lru_cache

MODEL_DIR = Path(__file__).parent / "models"

# Hashes SHA-256 esperados por modelo (gerar em treino: hashlib.sha256(open(path,"rb").read()).hexdigest())
MODEL_HASHES: dict[str, str] = {
    "classifier": "<sha256-do-classifier.joblib>",
    "regressor": "<sha256-do-regressor.joblib>",
}


def _verify_hash(path: Path, name: str) -> None:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = MODEL_HASHES.get(name)
    if expected and actual != expected:
        raise ValueError(f"Hash mismatch for model '{name}': ficheiro pode estar corrompido ou substituído")


class ModelRegistry:
    _instance = None
    _models: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, name: str):
        if name not in self._models:
            model_path = MODEL_DIR / f"{name}.joblib"
            _verify_hash(model_path, name)
            self._models[name] = joblib.load(model_path)
        return self._models[name]

    def get(self, name: str):
        return self._models.get(name)


@lru_cache()
def get_model_registry() -> ModelRegistry:
    return ModelRegistry()
```

## Inference Service

```python
# app/ml/inference.py
from app.ml.loader import get_model_registry
import numpy as np


class PredictionService:
    def __init__(self):
        self.registry = get_model_registry()

    def predict_classification(self, features: list[float]) -> dict:
        model = self.registry.load("classifier")
        input_data = np.array([features])

        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]

        return {
            "prediction": int(prediction),
            "confidence": float(max(probabilities)),
            "probabilities": probabilities.tolist()
        }

    def predict_regression(self, features: list[float]) -> dict:
        model = self.registry.load("regressor")
        input_data = np.array([features])

        prediction = model.predict(input_data)[0]

        return {
            "prediction": float(prediction)
        }
```

## Schemas

```python
# app/schemas/ml.py
from pydantic import BaseModel


class PredictionRequest(BaseModel):
    features: list[float]


class ClassificationResponse(BaseModel):
    prediction: int
    confidence: float
    probabilities: list[float]


class RegressionResponse(BaseModel):
    prediction: float
```

## Router

```python
# app/routers/predictions.py
from fastapi import APIRouter, HTTPException
from app.schemas.ml import PredictionRequest, ClassificationResponse, RegressionResponse
from app.ml.inference import PredictionService

router = APIRouter()


@router.post("/classify", response_model=ClassificationResponse)
async def classify(request: PredictionRequest):
    try:
        service = PredictionService()
        return service.predict_classification(request.features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regress", response_model=RegressionResponse)
async def regress(request: PredictionRequest):
    try:
        service = PredictionService()
        return service.predict_regression(request.features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Startup: Pre-load Models

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.ml.loader import get_model_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: carregar modelos
    registry = get_model_registry()
    registry.load("classifier")
    registry.load("regressor")
    print("✅ ML models loaded")

    yield  # App running

    # Shutdown: cleanup
    print("👋 Shutting down")


app = FastAPI(lifespan=lifespan)
```

## CPU-Bound: Thread Pool

```python
from fastapi import APIRouter
from concurrent.futures import ThreadPoolExecutor
import asyncio

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)


@router.post("/predict-heavy")
async def predict_heavy(request: PredictionRequest):
    loop = asyncio.get_event_loop()

    # Correr em thread separada para não bloquear
    result = await loop.run_in_executor(
        executor,
        lambda: heavy_prediction(request.features)
    )

    return result
```

## Regras

| Regra                     | Descrição                    |
| ------------------------- | ---------------------------- |
| Singleton para registry   | Modelos carregados uma vez   |
| Pre-load no startup       | Não carregar em cada request |
| ThreadPool para CPU-bound | Não bloquear event loop      |
| Schemas para I/O          | Validação de features        |
| Try/except nos endpoints  | Erros de inferência          |
