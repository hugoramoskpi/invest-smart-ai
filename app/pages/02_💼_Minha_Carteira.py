import streamlit as st
import pandas as pd
from database import engine, Ativo, Transacao
from sqlmodel import Session, select
from finance import calculate_portfolio_performance

st.set_page_config(page_title="Minha Carteira - InvestSmart", layout="wide")

st.header("💼 Detalhamento dos Ativos")

with Session(engine) as session:
    ativos = session.exec(select(Ativo)).all()
    dados_carteira = []
    for a in ativos:
        transacoes = session.exec(select(Transacao).where(Transacao.ativo_id == a.id)).all()
        dados_carteira.append({"ticker": a.ticker, "transacoes": transacoes})
        
if dados_carteira:
    perf_data, _, _ = calculate_portfolio_performance(dados_carteira)
    st.dataframe(pd.DataFrame(perf_data), use_container_width=True)
else:
    st.info("Nenhum ativo encontrado.")
