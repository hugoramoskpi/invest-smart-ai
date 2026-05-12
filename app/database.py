import os
from sqlmodel import SQLModel, create_engine, Session, Field
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuração da URL do Banco de Dados
# Se houver uma DATABASE_URL no .env, usa ela. Caso contrário, usa SQLite local.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./investimentos.db")

engine = create_engine(DATABASE_URL, echo=True)

class Ativo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    nome: str
    tipo: str  # Ações, FIIs, Cripto, etc.

class Transacao(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ativo_id: int = Field(foreign_key="ativo.id")
    data: datetime = Field(default_factory=datetime.utcnow)
    quantidade: float
    preco: float
    tipo_transacao: str  # Compra ou Venda

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
