from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database.connection import Base


# ── SQLAlchemy table ──────────────────────────────────────────────────────────

class CheckoutTable(Base):
    __tablename__ = "checkouts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    NomeCompleto = Column(String, nullable=False)
    saudacao = Column(String, nullable=True)
    quarto = Column(Integer, nullable=True)
    horaPartida = Column(DateTime, nullable=True)
    acompanhantes = Column(Integer, default=0)
    nPessoas = Column(Integer, default=1)
    idioma = Column(String, nullable=True)
    vitStatus = Column(String, nullable=True)
    obs = Column(String, nullable=True)
    isProcessed = Column(Boolean, default=False, nullable=False)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CheckoutCreate(BaseModel):
    NomeCompleto: str
    saudacao: Optional[str] = None
    quarto: Optional[int] = None
    horaPartida: Optional[datetime] = None
    acompanhantes: Optional[int] = 0
    nPessoas: Optional[int] = 1
    idioma: Optional[str] = None
    vitStatus: Optional[str] = None
    obs: Optional[str] = None


class CheckoutResponse(CheckoutCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isProcessed: bool = False


class UpdateObsRequest(BaseModel):
    obs: str
