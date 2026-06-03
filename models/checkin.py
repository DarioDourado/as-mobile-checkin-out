from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database.connection import Base


# ── SQLAlchemy table ──────────────────────────────────────────────────────────

class CheckinTable(Base):
    __tablename__ = "checkins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    NomeCompleto = Column(String, nullable=False)
    saudacao = Column(String, nullable=True)
    quarto = Column(Integer, nullable=True)
    horaChegada = Column(DateTime, nullable=True)
    acompanhantes = Column(Integer, default=0)
    nPessoas = Column(Integer, default=1)
    dataSaida = Column(DateTime, nullable=True)
    idioma = Column(String, nullable=True)
    vitStatus = Column(String, nullable=True)
    obs = Column(String, nullable=True)
    isProcessed = Column(Boolean, default=False, nullable=False)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CheckinCreate(BaseModel):
    NomeCompleto: str
    saudacao: Optional[str] = None
    quarto: Optional[int] = None
    horaChegada: Optional[datetime] = None
    acompanhantes: Optional[int] = 0
    nPessoas: Optional[int] = 1
    dataSaida: Optional[datetime] = None
    idioma: Optional[str] = None
    vitStatus: Optional[str] = None
    obs: Optional[str] = None


class CheckinResponse(CheckinCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isProcessed: bool = False


class UpdateObsRequest(BaseModel):
    obs: str
