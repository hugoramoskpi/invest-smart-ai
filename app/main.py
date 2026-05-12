import streamlit as st
from database import create_db_and_tables, engine, Ativo, Transacao
from sqlmodel import Session, select
import pandas as pd
import plotly.express as px
from finance import calculate_portfolio_performance

# Inicializa o banco de dados
create_db_and_tables()

st.set_page_config(page_title="InvestSmart", layout="wide", page_icon="📈")

# Estilo CSS customizado para um look mais moderno
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 InvestSmart: Seu Controle Inteligente")

# Sidebar
st.sidebar.title("Navegação")
page = st.sidebar.radio("Ir para:", ["Dashboard", "Minha Carteira", "Registrar Operação", "Assistente IA"])

if page == "Dashboard":
    # ... (restante do código do Dashboard)
    st.header("Resumo da Performance")
    
    with Session(engine) as session:
        ativos = session.exec(select(Ativo)).all()
        dados_carteira = []
        for a in ativos:
            transacoes = session.exec(select(Transacao).where(Transacao.ativo_id == a.id)).all()
            dados_carteira.append({"ticker": a.ticker, "transacoes": transacoes})
            
    if not dados_carteira or sum(len(d['transacoes']) for d in dados_carteira) == 0:
        st.info("Nenhuma transação encontrada. Comece registrando uma operação!")
    else:
        perf_data, total_inv, total_at = calculate_portfolio_performance(dados_carteira)
        df_perf = pd.DataFrame(perf_data)
        
        # Métricas no topo
        col1, col2, col3 = st.columns(3)
        lucro_total = total_at - total_inv
        rent_total = (lucro_total / total_inv * 100) if total_inv > 0 else 0
        
        col1.metric("Total Investido", f"R$ {total_inv:,.2f}")
        col2.metric("Valor Atual", f"R$ {total_at:,.2f}", f"{rent_total:.2f}%")
        col3.metric("Lucro/Prejuízo Total", f"R$ {lucro_total:,.2f}", delta_color="normal")

        st.markdown("---")
        
        # Gráficos
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Alocação por Ativo")
            fig_pie = px.pie(df_perf, values='Valor Atual', names='Ativo', hole=.4,
                            color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Lucro por Ativo (R$)")
            fig_bar = px.bar(df_perf, x='Ativo', y='P&L', 
                            color='P&L', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_bar, use_container_width=True)

elif page == "Minha Carteira":
    st.header("Detalhamento dos Ativos")
    with Session(engine) as session:
        ativos = session.exec(select(Ativo)).all()
        dados_carteira = []
        for a in ativos:
            transacoes = session.exec(select(Transacao).where(Transacao.ativo_id == a.id)).all()
            dados_carteira.append({"ticker": a.ticker, "transacoes": transacoes})
            
    if dados_carteira:
        perf_data, _, _ = calculate_portfolio_performance(dados_carteira)
        st.dataframe(pd.DataFrame(perf_data), use_container_width=True)

elif page == "Registrar Operação":
    st.header("Nova Transação")
    
    with Session(engine) as session:
        ativos = session.exec(select(Ativo)).all()
        lista_tickers = [a.ticker for a in ativos]
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("1. Cadastrar Novo Ativo")
        with st.form("novo_ativo"):
            new_ticker = st.text_input("Ticker (Ex: PETR4.SA)").upper()
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

elif page == "Assistente IA":
    st.header("🤖 Seu Assistente de Investimentos")
    st.write("Pergunte qualquer coisa sobre sua carteira atual.")
    
    with Session(engine) as session:
        ativos = session.exec(select(Ativo)).all()
        dados_carteira = []
        for a in ativos:
            transacoes = session.exec(select(Transacao).where(Transacao.ativo_id == a.id)).all()
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

st.sidebar.markdown("---")
st.sidebar.caption("v0.1.0 - InvestSmart AI Edition")
