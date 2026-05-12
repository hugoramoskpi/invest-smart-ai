import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from database import engine, Ativo, Transacao
from sqlmodel import Session, select
from finance import calculate_portfolio_performance, get_asset_metrics

st.set_page_config(page_title="Minha Carteira - InvestSmart", layout="wide")

st.header("💼 Detalhamento dos Ativos e Histórico")

with Session(engine) as session:
    ativos = session.exec(select(Ativo)).all()
    dados_carteira = []
    ativo_dict = {}
    
    for a in ativos:
        transacoes = session.exec(select(Transacao).where(Transacao.ativo_id == a.id)).all()
        if transacoes:
            # Incluímos o tipo para o gráfico de pizza por categoria
            dados_carteira.append({"ticker": a.ticker, "transacoes": transacoes, "tipo": a.tipo})
            ativo_dict[a.ticker] = {"tipo": a.tipo, "nome": a.nome, "transacoes": transacoes}
        
if not dados_carteira:
    st.info("Nenhuma transação encontrada. Comece registrando operações!")
else:
    perf_data, total_inv, total_at = calculate_portfolio_performance(dados_carteira)
    df_perf = pd.DataFrame(perf_data)
    
    # Mapeando os tipos para os ativos na performance
    tipos = {d["ticker"]: d["tipo"] for d in dados_carteira}
    df_perf["Tipo"] = df_perf["Ativo"].map(tipos)
    
    st.markdown("---")
    st.subheader("🎯 Alocação da Carteira")
    
    c1, c2 = st.columns(2)
    with c1:
        fig_pie_ativo = px.pie(df_perf, values="Valor Atual", names="Ativo", 
                               title="Por Ativo", hole=.4,
                               color_discrete_sequence=px.colors.qualitative.Safe)
        st.plotly_chart(fig_pie_ativo, use_container_width=True)
        
    with c2:
        # Agrupando por tipo (Ações, ETFs, FIIs, Cripto, etc.)
        df_tipo = df_perf.groupby("Tipo")["Valor Atual"].sum().reset_index()
        fig_pie_tipo = px.pie(df_tipo, values="Valor Atual", names="Tipo", 
                              title="Por Tipo de Investimento", hole=.4,
                              color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig_pie_tipo, use_container_width=True)
        
    st.markdown("---")
    st.subheader("📈 Análise Individual e Histórico de Compras")
    
    for item in perf_data:
        ticker = item["Ativo"]
        st.write(f"### {ticker} - {ativo_dict[ticker]['nome']}")
        
        # 1. Métricas Principais
        with st.spinner(f"Buscando métricas de {ticker}..."):
            metrics = get_asset_metrics([ticker])
            if metrics:
                m = metrics[0]
                m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)
                m_col1.metric("Preço Atual", f"R$ {m.get('Preço Atual', 'N/A')}")
                m_col2.metric("P/L (P/E)", m.get("P/L (P/E)", "N/A"))
                m_col3.metric("Div. Yield", f"{m.get('Div. Yield (%)', 'N/A')}%")
                m_col4.metric("ROIC", m.get("ROIC", "N/A"))
                m_col5.metric("Lucro Consec. (4A)", m.get("Lucro >0 (4A)?", "N/A"))
                m_col6.metric("Data IPO", m.get("Data IPO", "N/A"))
        
        # 2. Gráfico Histórico com Pontos de Compra
        with st.spinner(f"Carregando histórico de {ticker}..."):
            try:
                # Usa 5 anos para dar uma visão ampla
                t = yf.Ticker(ticker)
                hist = t.history(period="5y")
                
                if not hist.empty:
                    fig = go.Figure()
                    
                    # Linha do preço histórico
                    fig.add_trace(go.Scatter(
                        x=hist.index, 
                        y=hist['Close'], 
                        mode='lines', 
                        name='Cotação', 
                        line=dict(color='#58a6ff', width=2)
                    ))
                    
                    # Adiciona os pontos de compra
                    transacoes = ativo_dict[ticker]["transacoes"]
                    compras = [t for t in transacoes if t.tipo_transacao == "Compra"]
                    vendas = [t for t in transacoes if t.tipo_transacao == "Venda"]
                    
                    if compras:
                        buy_dates = [t.data for t in compras]
                        buy_prices = [t.preco for t in compras]
                        buy_texts = [f"COMPRA<br>Data: {t.data.strftime('%d/%m/%Y')}<br>Qtd: {t.quantidade}<br>Preço: R${t.preco}" for t in compras]
                        
                        fig.add_trace(go.Scatter(
                            x=buy_dates, 
                            y=buy_prices, 
                            mode='markers', 
                            name='Minhas Compras',
                            marker=dict(color='#2ea043', size=12, symbol='triangle-up', line=dict(color='white', width=1)),
                            text=buy_texts,
                            hoverinfo='text'
                        ))
                        
                    if vendas:
                        sell_dates = [t.data for t in vendas]
                        sell_prices = [t.preco for t in vendas]
                        sell_texts = [f"VENDA<br>Data: {t.data.strftime('%d/%m/%Y')}<br>Qtd: {t.quantidade}<br>Preço: R${t.preco}" for t in vendas]
                        
                        fig.add_trace(go.Scatter(
                            x=sell_dates, 
                            y=sell_prices, 
                            mode='markers', 
                            name='Minhas Vendas',
                            marker=dict(color='#f85149', size=12, symbol='triangle-down', line=dict(color='white', width=1)),
                            text=sell_texts,
                            hoverinfo='text'
                        ))
                    
                    fig.update_layout(
                        title=f"Histórico de Cotação (5 anos) e Operações - {ticker}",
                        xaxis_title="Data",
                        yaxis_title="Preço (R$)",
                        template="plotly_dark",
                        hovermode="x unified",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"Não foi possível carregar o histórico de cotações para {ticker}.")
            except Exception as e:
                st.error(f"Erro ao gerar gráfico de {ticker}: {e}")
                
        st.markdown("<br><hr><br>", unsafe_allow_html=True)
