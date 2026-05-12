import streamlit as st
import pandas as pd
import plotly.express as px
from database import engine, Ativo, Transacao
from sqlmodel import Session, select
from finance import calculate_portfolio_performance

st.set_page_config(page_title="Dashboard - InvestSmart", layout="wide")

st.header("📊 Resumo da Performance")

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
