import streamlit as st
import pandas as pd
from database import engine, Ativo, Transacao
from sqlmodel import Session, select

st.set_page_config(page_title="Registrar Operação - InvestSmart", layout="wide")

st.header("📝 Nova Transação")

TICKERS_COMUNS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA", "MGLU3.SA", "BBAS3.SA",
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX",
    "IVVB11.SA", "BOVA11.SA", "SMAL11.SA",
    "BTC-USD", "ETH-USD"
]

with Session(engine) as session:
    ativos = session.exec(select(Ativo)).all()
    lista_tickers = [a.ticker for a in ativos]

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("1. Cadastrar Novo Ativo")
    ticker_sugestao = st.selectbox("Sugestões de Tickers (Auto-complete)", [""] + TICKERS_COMUNS)
    
    with st.form("novo_ativo"):
        new_ticker = st.text_input("Ticker (Ex: PETR4.SA)", value=ticker_sugestao).upper()
        new_nome = st.text_input("Nome da Empresa")
        new_tipo = st.selectbox("Tipo", ["Ações", "FIIs", "Cripto", "BDRs", "ETFs"])
        if st.form_submit_button("Cadastrar Ativo"):
            with Session(engine) as session:
                session.add(Ativo(ticker=new_ticker, nome=new_nome, tipo=new_tipo))
                session.commit()
                st.success(f"{new_ticker} cadastrado!")
                st.rerun()

with col_b:
    st.subheader("2. Registrar Compra/Venda")
    if not lista_tickers:
        st.warning("Cadastre um ativo primeiro.")
    else:
        with st.form("nova_transacao"):
            sel_ticker = st.selectbox("Selecione o Ativo", lista_tickers)
            data_op = st.date_input("Data da Operação")
            qtd = st.number_input("Quantidade", min_value=0.01)
            preco = st.number_input("Preço Unitário (R$)", min_value=0.01)
            tipo_op = st.radio("Tipo", ["Compra", "Venda"])
            
            if st.form_submit_button("Registrar Transação"):
                with Session(engine) as session:
                    ativo_db = session.exec(select(Ativo).where(Ativo.ticker == sel_ticker)).first()
                    nova_t = Transacao(
                        ativo_id=ativo_db.id,
                        data=pd.to_datetime(data_op),
                        quantidade=qtd,
                        preco=preco,
                        tipo_transacao=tipo_op
                    )
                    session.add(nova_t)
                    session.commit()
                    st.success("Operação registrada!")
