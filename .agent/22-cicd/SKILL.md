# CI/CD - GitHub Actions

## Estratégia

```
Push → Lint + Type + Security scan + Test + Coverage → Build Docker → Push GHCR → Deploy
```

## Estrutura

```
.github/
└── workflows/
    ├── ci.yml       # Lint, testes, coverage
    └── cd.yml       # Build Docker + deploy
```

## CI Pipeline (ci.yml)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Lint (ruff)
        run: ruff check app tests

      - name: Type check (mypy)
        run: mypy app

      - name: Security scan (bandit)
        run: bandit -r app -ll -q
        # -ll = reporta apenas Medium e High; -q = output limpo

      - name: Dependency audit (pip-audit)
        run: pip-audit --require-hashes -r requirements.txt
        # Falha se houver CVEs conhecidas nas dependências

      - name: Run tests + coverage
        env:
          DATABASE_URL: sqlite+aiosqlite:///:memory:
          SECRET_KEY: ci-test-secret-key-32chars-minimum
          PRODUCTION: "false"
        run: pytest --cov=app --cov-report=xml --cov-fail-under=70 -q
        # --cov-fail-under=70 bloqueia o PR se coverage < 70%

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage.xml
```

## CD Pipeline (cd.yml)

```yaml
# .github/workflows/cd.yml
name: CD

on:
  push:
    branches: [main]
    tags: ["v*.*.*"]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha,prefix=sha-

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_KEY }}
          script: |
            cd /app
            docker compose pull api
            docker compose up -d api
            docker compose exec api alembic upgrade head
```

## requirements-dev.txt

```
pytest
pytest-asyncio
pytest-cov
httpx
factory-boy
ruff
mypy
bandit[toml]     # análise estática de segurança
pip-audit        # scan de dependências vulneráveis (CVEs)
```

## Secrets no GitHub

| Secret             | Valor                              |
| ------------------ | ---------------------------------- |
| `SECRET_KEY`       | Chave JWT de produção              |
| `DATABASE_URL`     | URL da base de dados de produção   |
| `DEPLOY_HOST`      | IP/hostname do servidor            |
| `DEPLOY_USER`      | Utilizador SSH                     |
| `DEPLOY_KEY`       | Chave privada SSH                  |
| `CODECOV_TOKEN`    | Token do Codecov (opcional)        |

## Branch Protection Rules (configurar no GitHub)

```
Settings → Branches → Add branch protection rule para main:
  ✅ Require status checks to pass before merging
      → test (Lint, Type check, Security scan, Dependency audit, Tests + coverage)
  ✅ Require branches to be up to date before merging
  ✅ Require pull request reviews before merging (1 reviewer)
  ✅ Dismiss stale pull request approvals when new commits are pushed
  ✅ Do not allow bypassing the above settings
```

## Regras

| Regra                                       | Motivo                          |
| ------------------------------------------- | ------------------------------- |
| Nunca commitar `.env` ou secrets            | Segurança                       |
| `alembic upgrade head` no deploy            | Migrations automáticas          |
| Cache Docker layers no GitHub Actions       | Build mais rápido               |
| `environment: production` no job de deploy  | Aprovação manual opcional       |
| Testes + bandit + pip-audit passam antes de deploy | Qualidade + segurança garantidas |
| Branch protection activa em main            | Impede merge directo sem CI     |
