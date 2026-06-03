"""
Popula a base de dados com 15 checkins e 15 checkouts de teste.
Executa com:  python seed.py
"""
from datetime import datetime, timedelta
import random

from database.connection import SessionLocal, Base, engine
from models.checkin import CheckinTable
from models.checkout import CheckoutTable

# Garante que as tabelas existem
Base.metadata.create_all(bind=engine)

NOMES = [
    "Ana Silva", "João Ferreira", "Maria Santos", "Carlos Oliveira", "Sofia Costa",
    "Pedro Rodrigues", "Inês Martins", "Tiago Sousa", "Beatriz Alves", "Rui Pereira",
    "Catarina Gomes", "André Ribeiro", "Mariana Neves", "Francisco Lima", "Laura Carvalho",
]

SAUDACOES = ["Bom dia", "Boa tarde", "Boa noite"]
IDIOMAS = ["PT", "EN", "ES", "FR", "DE"]
VIT_STATUS = ["VIP", "Normal", "Gold", "Silver"]
QUARTOS = list(range(101, 320))

base_date = datetime(2026, 6, 3, 10, 0, 0)

CHECKINS = [
    CheckinTable(
        NomeCompleto=NOMES[i],
        saudacao=random.choice(SAUDACOES),
        quarto=random.choice(QUARTOS),
        horaChegada=base_date + timedelta(hours=i * 2),
        acompanhantes=random.randint(0, 3),
        nPessoas=random.randint(1, 4),
        dataSaida=base_date + timedelta(days=random.randint(1, 7)),
        idioma=random.choice(IDIOMAS),
        vitStatus=random.choice(VIT_STATUS),
        obs=f"Observação checkin {i + 1}" if i % 3 == 0 else None,
        isProcessed=i < 7,   # primeiros 7 já processados, restantes pendentes
    )
    for i in range(15)
]

CHECKOUTS = [
    CheckoutTable(
        NomeCompleto=NOMES[i],
        saudacao=random.choice(SAUDACOES),
        quarto=random.choice(QUARTOS),
        horaPartida=base_date + timedelta(hours=i * 2 + 1),
        acompanhantes=random.randint(0, 3),
        nPessoas=random.randint(1, 4),
        idioma=random.choice(IDIOMAS),
        vitStatus=random.choice(VIT_STATUS),
        obs=f"Observação checkout {i + 1}" if i % 4 == 0 else None,
        isProcessed=i < 6,   # primeiros 6 já processados, restantes pendentes
    )
    for i in range(15)
]

db = SessionLocal()
try:
    db.add_all(CHECKINS)
    db.add_all(CHECKOUTS)
    db.commit()
    print(f"✓ {len(CHECKINS)} checkins inseridos")
    print(f"✓ {len(CHECKOUTS)} checkouts inseridos")
finally:
    db.close()
