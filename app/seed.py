from database import engine, Ativo, Transacao
from sqlmodel import Session, select
from datetime import datetime, timedelta

def seed_db():
    with Session(engine) as session:
        ativos = session.exec(select(Ativo)).all()
        if not ativos:
            # Base imaginária para testes
            a1 = Ativo(ticker="PETR4.SA", nome="Petrobras", tipo="Ações")
            a2 = Ativo(ticker="AAPL", nome="Apple", tipo="Ações")
            a3 = Ativo(ticker="IVVB11.SA", nome="S&P 500", tipo="ETFs")
            
            session.add_all([a1, a2, a3])
            session.commit()
            
            t1 = Transacao(ativo_id=a1.id, data=datetime.now() - timedelta(days=30), quantidade=100, preco=35.50, tipo_transacao="Compra")
            t2 = Transacao(ativo_id=a2.id, data=datetime.now() - timedelta(days=60), quantidade=10, preco=170.00, tipo_transacao="Compra")
            t3 = Transacao(ativo_id=a3.id, data=datetime.now() - timedelta(days=15), quantidade=50, preco=250.00, tipo_transacao="Compra")
            
            session.add_all([t1, t2, t3])
            session.commit()
