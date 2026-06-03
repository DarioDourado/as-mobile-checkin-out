# MIGRATIONS - Alembic

## Setup

```bash
pip install alembic
alembic init alembic
```

## Configuração

```python
# alembic/env.py
from app.database import SQLALCHEMY_DATABASE_URL
from app.models.base import Base
# Importar todos os models
from app.models import user, post

target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=SQLALCHEMY_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(
        SQLALCHEMY_DATABASE_URL.replace("+aiosqlite", "")  # Sync para migrations
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

```ini
# alembic.ini
sqlalchemy.url = sqlite:///./sqlite.db
```

## Comandos

```bash
# Criar migration
alembic revision --autogenerate -m "create users table"

# Aplicar migrations
alembic upgrade head

# Reverter
alembic downgrade -1

# Ver histórico
alembic history

# Ver current
alembic current
```

## Migration Exemplo

```python
# alembic/versions/001_create_users_table.py
from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "user", name="user_role"), default="user"),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
    )


def downgrade():
    op.drop_table("users")
```

## SQLite → MySQL

```ini
# alembic.ini (dev)
sqlalchemy.url = sqlite:///./sqlite.db

# alembic.ini (prod) - ou via env var
sqlalchemy.url = mysql+pymysql://user:pass@host/dbname
```

## Regras

| Regra                           | Descrição                   |
| ------------------------------- | --------------------------- |
| `--autogenerate`                | Detectar mudanças no schema |
| Nunca editar migrations antigas | Criar nova                  |
| Importar todos os models        | Em `env.py`                 |
| Sync engine para migrations     | Alembic não suporta async   |
| Testar upgrade + downgrade      | Antes de commit             |
