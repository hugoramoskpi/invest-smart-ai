import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from database import engine, Ativo, Transacao
from sqlmodel import Session, select
from finance import calculate_portfolio_performance, get_asset_metrics, METRICS_HELP
from style import apply_global_style

st.set_page_config(page_title="Minha Carteira - InvestSmart", layout="wide", page_icon="💼")

# Aplica o Estilo Unificado
apply_global_style()

tab1, tab2 = st.tabs(["💼 Minha Carteira", "🧪 Estudos (Watchlist)"])

with tab1:
    st.header("💼 Detalhamento dos Ativos e Histórico")

    with Session(engine) as session:
        ativos = session.exec(select(Ativo)).all()
        dados_carteira = []
        ativo_dict = {}
        
        for a in ativos:
            transacoes = session.exec(select(Transacao).where(Transacao.ativo_id == a.id)).all()
            if transacoes:
                # Calcula quantidade para ver se remove da aba de estudos
                qtd_total = sum(t.quantidade for t in transacoes if t.tipo_transacao == "Compra")
                qtd_total -= sum(t.quantidade for t in transacoes if t.tipo_transacao == "Venda")
                
                if qtd_total > 0:
                    dados_carteira.append({"ticker": a.ticker, "transacoes": transacoes, "tipo": a.tipo})
                    ativo_dict[a.ticker] = {"tipo": a.tipo, "nome": a.nome, "transacoes": transacoes}
            
    if not dados_carteira:
        st.info("Nenhuma transação encontrada ou carteira zerada. Registre operações para ver o detalhamento!")
    else:
        perf_data, total_inv, total_at = calculate_portfolio_performance(dados_carteira)
        df_perf = pd.DataFrame(perf_data)
        
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
            
            with st.spinner(f"Buscando métricas de {ticker}..."):
                metrics = get_asset_metrics([ticker])
                if metrics:
                    m = metrics[0]
                    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6 = st.columns(6)

                    # Preço
                    m_col1.metric("Preço Atual", f"R$ {m.get('Preço Atual', 'N/A')}", help=METRICS_HELP["Preço Atual"])

                    # P/L
                    pl_val = m.get("P/L (P/E)")
                    m_col2.metric("P/L (P/E)", f"{pl_val:.2f}" if isinstance(pl_val, (int, float)) else "N/A", help=METRICS_HELP["P/L (P/E)"])

                    # Dividend Yield
                    dy_val = m.get("Div. Yield (%)")
                    m_col3.metric("Div. Yield", f"{dy_val:.2f}%" if isinstance(dy_val, (int, float)) else "N/A", help=METRICS_HELP["Div. Yield (%)"])

                    # ROIC
                    roic_val = m.get("ROIC (%)")
                    m_col4.metric("ROIC", f"{roic_val:.2f}%" if isinstance(roic_val, (int, float)) else "N/A", help=METRICS_HELP["ROIC (%)"])

                    # Lucro Consecutivo
                    m_col5.metric("Lucro Consec. (4A)", m.get("Lucro >0 (4A)?", "N/A"), help=METRICS_HELP["Lucro >0 (4A)?"])

                    # IPO
                    m_col6.metric("Data IPO", m.get("Data IPO", "N/A"), help=METRICS_HELP["Data IPO"])
            with st.spinner(f"Carregando histórico de {ticker}..."):
                try:
                    t = yf.Ticker(ticker)
                    hist = t.history(period="5y")
                    if not hist.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Cotação', line=dict(color='#58a6ff', width=2)))
                        
                        transacoes = ativo_dict[ticker]["transacoes"]
                        compras = [t for t in transacoes if t.tipo_transacao == "Compra"]
                        vendas = [t for t in transacoes if t.tipo_transacao == "Venda"]
                        
                        if compras:
                            fig.add_trace(go.Scatter(x=[t.data for t in compras], y=[t.preco for t in compras], mode='markers', name='Compras',
                                marker=dict(color='#2ea043', size=12, symbol='triangle-up', line=dict(color='white', width=1)),
                                text=[f"Data: {t.data.strftime('%d/%m/%Y')}<br>Qtd: {t.quantidade}" for t in compras], hoverinfo='text'))
                        if vendas:
                            fig.add_trace(go.Scatter(x=[t.data for t in vendas], y=[t.preco for t in vendas], mode='markers', name='Vendas',
                                marker=dict(color='#f85149', size=12, symbol='triangle-down', line=dict(color='white', width=1)),
                                text=[f"Data: {t.data.strftime('%d/%m/%Y')}<br>Qtd: {t.quantidade}" for t in vendas], hoverinfo='text'))
                        
                        fig.update_layout(title=f"Histórico e Operações - {ticker}", template="plotly_dark", hovermode="x unified")
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    st.error(f"Erro ao carregar gráfico de {ticker}")
            st.markdown("<br><hr><br>", unsafe_allow_html=True)

with tab2:
    st.header("🧪 Área de Estudos (Favoritos)")
    st.write("Ativos favoritados que você ainda não possui na carteira.")
    
    with Session(engine) as session:
        # Busca ativos favoritados
        estudos = session.exec(select(Ativo).where(Ativo.favorito == True)).all()
        lista_estudos = []
        
        for e in estudos:
            # Verifica se já tem transação (se já comprou, some daqui)
            trans = session.exec(select(Transacao).where(Transacao.ativo_id == e.id)).all()
            total_investido = sum(t.quantidade for t in trans if t.tipo_transacao == "Compra")
            if total_investido == 0:
                lista_estudos.append(e.ticker)
        
        if not lista_estudos:
            st.info("Nenhum ativo em estudo no momento. Favorite ativos na aba de Comparação!")
        else:
            with st.spinner("Buscando dados das empresas em estudo..."):
                metrics_estudos = get_asset_metrics(lista_estudos)
                df_estudos = pd.DataFrame(metrics_estudos)
                
                # Renderização formatada
                st.dataframe(
                    df_estudos.style.format({
                        "Preço Atual": "R$ {:.2f}",
                        "P/L (P/E)": "{:.2f}",
                        "P/VP (P/B)": "{:.2f}",
                        "Div. Yield (%)": "{:.2f}%",
                        "Market Cap": lambda x: f"B$ {x/1e9:.2f}B" if pd.notnull(x) and x > 0 else "N/A",
                        "ROE (%)": "{:.2f}%",
                        "ROIC (%)": "{:.2f}%"
                    }, na_rep="N/A"),
                    column_config={k: st.column_config.Column(help=v) for k, v in METRICS_HELP.items()},
                    use_container_width=True
                )
                
                for ticker in lista_estudos:
                    if st.button(f"Remover {ticker} dos Estudos", key=f"rem_{ticker}"):
                        ativo_db = session.exec(select(Ativo).where(Ativo.ticker == ticker)).first()
                        ativo_db.favorito = False
                        session.add(ativo_db)
                        session.commit()
                        st.rerun()

st.sidebar.caption("v0.4.3 - InvestSmart AI Edition")
