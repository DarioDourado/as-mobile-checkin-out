# DOCKER - Containerização

## Ficheiros

```
project/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── .dockerignore
└── requirements.txt
```

## Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 8000

# Comando
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose (Dev)

```yaml
# docker-compose.yml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=sqlite:///./sqlite.db
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=http://localhost:3000
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - db

  db:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

## Docker Compose (Prod)

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - PRODUCTION=true
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    depends_on:
      - db

  db:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

## .dockerignore

```
__pycache__
*.pyc
*.pyo
.git
.env
.venv
venv
*.db
.pytest_cache
.mypy_cache
```

## requirements.txt

```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
aiomysql>=0.2.0
alembic>=1.12.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.0
python-multipart>=0.0.6
faker>=19.0.0
```

## Comandos

```bash
# Dev
docker-compose up

# Prod
docker-compose -f docker-compose.prod.yml up --build -d

# Logs
docker-compose logs -f api

# Shell
docker-compose exec api bash

# Migrations dentro do container
docker-compose exec api alembic upgrade head
```

## Regras

| Regra                    | Descrição           |
| ------------------------ | ------------------- |
| `--reload` apenas em dev | Não em prod         |
| `--workers` em prod      | Múltiplos workers   |
| Volumes para DB          | Persistência        |
| `.dockerignore`          | Excluir **pycache** |
| Secrets via env          | Não hardcoded       |
