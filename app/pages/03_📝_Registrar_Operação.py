import streamlit as st
import pandas as pd
from database import engine, Ativo, Transacao
from sqlmodel import Session, select
from finance import get_asset_basic_info, get_historical_price

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
    # Auto-complete com sugestões
    ticker_sugestao = st.selectbox("Sugestões de Tickers (Auto-complete)", [""] + TICKERS_COMUNS)
    
    # Input reativo do Ticker
    new_ticker = st.text_input("Ticker (Ex: PETR4.SA)", value=ticker_sugestao).upper()
    
    # Busca automática se houver ticker
    auto_info = {"nome": "", "tipo": "Ações"}
    if new_ticker:
        with st.spinner("Buscando info do ativo..."):
            auto_info = get_asset_basic_info(new_ticker)
            
    with st.form("novo_ativo"):
        new_nome = st.text_input("Nome da Empresa", value=auto_info["nome"])
        new_tipo = st.selectbox("Tipo", ["Ações", "FIIs", "Cripto", "BDRs", "ETFs"], 
                               index=["Ações", "FIIs", "Cripto", "BDRs", "ETFs"].index(auto_info["tipo"]))
        
        if st.form_submit_button("Cadastrar Ativo"):
            if not new_ticker:
                st.error("Digite um ticker.")
            else:
                with Session(engine) as session:
                    # Verifica se já existe
                    existente = session.exec(select(Ativo).where(Ativo.ticker == new_ticker)).first()
                    if existente:
                        st.warning(f"O ativo {new_ticker} já está cadastrado.")
                    else:
                        session.add(Ativo(ticker=new_ticker, nome=new_nome, tipo=new_tipo))
                        session.commit()
                        st.success(f"{new_ticker} cadastrado!")
                        st.rerun()

with col_b:
    st.subheader("2. Registrar Compra/Venda")
    if not lista_tickers:
        st.warning("Cadastre um ativo primeiro.")
    else:
        # Inputs reativos para buscar preço
        sel_ticker = st.selectbox("Selecione o Ativo", lista_tickers)
        data_op = st.date_input("Data da Operação")
        
        auto_preco = 0.0
        if sel_ticker and data_op:
            with st.spinner(f"Buscando preço de {sel_ticker} em {data_op}..."):
                auto_preco = get_historical_price(sel_ticker, data_op)
                if auto_preco == 0.0:
                    st.caption("Preço não encontrado para esta data (pode ser feriado/final de semana).")

        with st.form("nova_transacao"):
            qtd = st.number_input("Quantidade", min_value=0.01)
            preco = st.number_input("Preço Unitário (R$)", min_value=0.0, value=auto_preco)
            tipo_op = st.radio("Tipo", ["Compra", "Venda"])
            
            if st.form_submit_button("Registrar Transação"):
                if preco <= 0:
                    st.error("Preço deve ser maior que zero.")
                else:
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
