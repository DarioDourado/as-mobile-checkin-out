# CORS - Cross-Origin Resource Sharing

## Propósito

Permitir que o frontend React/React Native comunique com o backend FastAPI de um domínio diferente.

## Instalação

O CORS já vem com FastAPI, basta configurar.

## Configuração

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # Para cookies httpOnly
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
```

## Settings

```python
# app/config/settings.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    class Config:
        env_file = ".env"

settings = Settings()
```

## Environment Variables

```bash
# .env
CORS_ORIGINS=["http://localhost:3000","https://meuapp.com"]
```

## Produção

```python
# Mais restritivo em produção
CORS_ORIGINS: List[str] = [
    "https://meuapp.com",
    "https://www.meuapp.com",
]
```

## Regras

| Regra                    | Descrição                 |
| ------------------------ | ------------------------- |
| `allow_credentials=True` | Obrigatório para cookies  |
| Origins específicos      | Nunca `["*"]` em produção |
| Methods explícitos       | Listar apenas os usados   |
| Settings dinâmicos       | Via `.env`                |
