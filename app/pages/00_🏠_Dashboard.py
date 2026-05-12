import streamlit as st
import pandas as pd
import plotly.express as px
from database import engine, Ativo, Transacao, create_db_and_tables
from sqlmodel import Session, select
from finance import calculate_portfolio_performance
from seed import seed_db

# Inicializa o banco de dados e a base imaginária na Home
create_db_and_tables()
seed_db()

st.set_page_config(
    page_title="Dashboard - InvestSmart",
    layout="wide",
    page_icon="📊"
)

# Estilo CSS Avançado para o Menu Lateral e Interface
st.markdown("""
    <style>
    /* Estilização do Menu Lateral */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    section[data-testid="stSidebar"] .st-emotion-cache-16t9854 {
        color: #c9d1d9;
    }

    /* Melhora o espaçamento da navegação */
    [data-testid="stSidebarNav"] ul {
        padding-top: 1rem;
    }
    
    [data-testid="stSidebarNav"] li a span {
        font-weight: 500;
        font-size: 1.05rem;
    }

    /* Esconde especificamente o link redundante 'main' se ele aparecer */
    [data-testid="stSidebarNav"] li:first-child {
        display: none;
    }

    /* Estilo dos Cards de Métrica */
    div[data-testid="stMetric"] {
        background-color: #0d1117;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #58a6ff;
    }

    /* Botões principais */
    .stButton>button {
        border-radius: 8px;
        background-color: #238636;
        color: white;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# Título e Logo no Menu Lateral
st.sidebar.markdown("""
    <div style="text-align: center; padding-bottom: 20px;">
        <h1 style='color: #58a6ff; font-size: 2.2rem;'>🚀</h1>
        <h2 style='color: #c9d1d9; font-size: 1.2rem; margin-top: -10px;'>InvestSmart</h2>
        <p style='color: #8b949e; font-size: 0.8rem;'>Controle de Investimentos</p>
    </div>
    <hr style="margin: 10px 0; border-color: #30363d;">
    """, unsafe_allow_html=True)

st.title("📊 Dashboard Geral da Carteira")

with Session(engine) as session:
    ativos = session.exec(select(Ativo)).all()
    dados_carteira = []
    for a in ativos:
        transacoes = session.exec(select(Transacao).where(Transacao.ativo_id == a.id)).all()
        if transacoes:
            dados_carteira.append({"ticker": a.ticker, "transacoes": transacoes})
        
if not dados_carteira:
    st.info("Nenhuma transação encontrada. Comece registrando uma operação no menu lateral!")
else:
    perf_data, total_inv, total_at = calculate_portfolio_performance(dados_carteira)
    df_perf = pd.DataFrame(perf_data)
    
    # Métricas Principais (Topo)
    lucro_total = total_at - total_inv
    rent_total = (lucro_total / total_inv * 100) if total_inv > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Investimento Total", f"R$ {total_inv:,.2f}")
    c2.metric("Valor de Mercado", f"R$ {total_at:,.2f}")
    c3.metric("Lucro/Prejuízo Absoluto", f"R$ {lucro_total:,.2f}", f"{rent_total:.2f}%")
    c4.metric("Qtd de Ativos", len(df_perf))

    st.markdown("---")
    
    # Seção de Alocação e Performance Visual
    col_v1, col_v2 = st.columns([1, 1])
    
    with col_v1:
        st.subheader("🎯 Alocação da Carteira")
        fig_pie = px.pie(df_perf, values='Valor Atual', names='Ativo', hole=.4,
                        color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_v2:
        st.subheader("📈 Performance por Ativo (P&L)")
        fig_bar = px.bar(df_perf, x='Ativo', y='P&L', 
                        color='P&L', color_continuous_scale='RdYlGn',
                        text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    
    # Tabela Detalhada (Todos os Ativos e Métricas)
    st.subheader("📋 Visão Detalhada dos Ativos")
    
    # Adicionando barra de progresso de lucro por ativo
    st.dataframe(
        df_perf.style.format({
            "Custo Médio": "R$ {:.2f}",
            "Preço Atual": "R$ {:.2f}",
            "Valor Atual": "R$ {:.2f}",
            "P&L": "R$ {:.2f}",
            "Rentab. (%)": "{:.2f}%"
        }).background_gradient(subset=["Rentab. (%)"], cmap="RdYlGn"),
        use_container_width=True
    )
    
    # Gráfico de Evolução
    st.subheader("📊 Comparativo de Rentabilidade (%)")
    fig_rent = px.bar(df_perf, x="Ativo", y="Rentab. (%)", color="Rentab. (%)", 
                      color_continuous_scale="Viridis", title="Rentabilidade Percentual por Ativo")
    st.plotly_chart(fig_rent, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("v0.4.1 - InvestSmart AI Edition")
