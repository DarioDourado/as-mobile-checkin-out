from fastapi import FastAPI

from database.connection import Base, engine
from models import checkin, checkout  # noqa: F401 — regista os modelos no metadata
from routes.checkins import router as checkins_router
from routes.checkouts import router as checkouts_router

# Cria as tabelas na base de dados se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hotel API")

app.include_router(checkins_router)
app.include_router(checkouts_router)


@app.get("/")
async def read_root():
    return {"message": "Hotel API online"}


@app.get("/health")
async def health():
    return {"status": "ok"}
