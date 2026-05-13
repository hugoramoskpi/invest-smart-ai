import os
from sqlmodel import SQLModel, create_engine, Session, Field
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuração da URL do Banco de Dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./investimentos.db")

# O check_same_thread=False é necessário apenas para o SQLite quando usado com Streamlit
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)

class Ativo(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    nome: str
    tipo: str  # Ações, FIIs, Cripto, etc.
    favorito: bool = Field(default=False)

class Transacao(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    ativo_id: int = Field(foreign_key="ativo.id")
    data: datetime = Field(default_factory=datetime.utcnow)
    quantidade: float
    preco: float
    tipo_transacao: str  # Compra ou Venda

class MetaAlocacao(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(unique=True) # Classe de ativo (ex: Ações) ou Ticker (ex: AAPL)
    alvo_percentual: float 
    categoria: str # "Classe" ou "Ativo"

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
