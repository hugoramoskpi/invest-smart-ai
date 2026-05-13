import streamlit as st
from database import engine, Ativo, Transacao
from sqlmodel import Session, select
from finance import calculate_portfolio_performance
from agent.invest_agent import InvestAgent
from style import apply_global_style

st.set_page_config(page_title="Assistente IA - InvestSmart", layout="wide", page_icon="🤖")

# Aplica o Estilo Unificado
apply_global_style()

st.header("🤖 Seu Assistente de Investimentos")
st.write("Pergunte qualquer coisa sobre sua carteira atual.")

with Session(engine) as session:
    ativos = session.exec(select(Ativo)).all()
    dados_carteira = []
    for a in ativos:
        transacoes = session.exec(select(Transacao).where(Transacao.ativo_id == a.id)).all()
        if transacoes:
            dados_carteira.append({"ticker": a.ticker, "transacoes": transacoes})
        
if not dados_carteira:
    st.info("Você precisa ter ativos registrados para usar o assistente.")
else:
    perf_data, _, _ = calculate_portfolio_performance(dados_carteira)
    contexto = str(perf_data)
    
    agent = InvestAgent()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Exibe mensagens anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input do usuário
    if prompt := st.chat_input("Ex: Como está a minha rentabilidade total?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = agent.ask(prompt, contexto)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

st.sidebar.caption("v0.4.3 - InvestSmart AI Edition")
