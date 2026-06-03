# API FastAPI — quick start

Pré-requisitos:

- Python 3.8+ (recomenda-se 3.11+)
- Virtualenv criado e activo (veja `venv/`)

Instalar dependências (com venv activo):

```bash
pip install -r requirements.txt
```

Executar em desenvolvimento (uvicorn):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
