import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from finance import get_asset_metrics, METRICS_HELP
from database import engine, Ativo
from sqlmodel import Session, select
from style import apply_global_style
from screener_tickers import ALL_SCREENER_TICKERS, TICKERS_IBOVESPA, TICKERS_SP500_TOP

st.set_page_config(page_title="Comparação de Ativos - InvestSmart", layout="wide", page_icon="⚖️")

# Aplica o Estilo Unificado
apply_global_style()

st.title("⚖️ Comparação de Ativos (Brasil e EUA)")
st.write("Compare métricas fundamentalistas e filtre os melhores ativos em tempo real.")

TICKERS_COMUNS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA", "MGLU3.SA", "BBAS3.SA",
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX",
    "IVVB11.SA", "BOVA11.SA", "SMAL11.SA"
]

# --- CONFIGURAÇÃO DOS FILTROS DINÂMICOS (SIDEBAR) ---
st.sidebar.header("🔍 Filtros Reativos")

current_year = datetime.datetime.now().year
# Janela Móvel IPO (1800 até hoje)
ano_ipo = st.sidebar.slider("Janela Data de IPO", 1800, current_year, (1800, current_year), help=METRICS_HELP["Data IPO"])

# Sliders para métricas numéricas
pl_max = st.sidebar.slider("P/L (P/E) Máximo", -50.0, 200.0, 200.0, help=METRICS_HELP["P/L (P/E)"])
pvp_max = st.sidebar.slider("P/VP (P/B) Máximo", -10.0, 100.0, 100.0, help=METRICS_HELP["P/VP (P/B)"])

min_roic = st.sidebar.slider("ROIC Mínimo (%)", -50.0, 150.0, -50.0, help=METRICS_HELP["ROIC (%)"])
min_roe = st.sidebar.slider("ROE Mínimo (%)", -50.0, 150.0, -50.0, help=METRICS_HELP["ROE (%)"])
min_dividend = st.sidebar.slider("Div. Yield Mínimo (%)", 0.0, 50.0, 0.0, help=METRICS_HELP["Div. Yield (%)"])

# Market Cap em Bilhões
min_mcap_b = st.sidebar.number_input("Market Cap Mín. (Bilhões R$/$)", min_value=0.0, value=0.0, help=METRICS_HELP["Market Cap"])

# Filtros Booleanos
lucro_apenas = st.sidebar.checkbox("Apenas empresas com Lucro (4A)", value=False, help=METRICS_HELP["Lucro >0 (4A)?"])
receita_crescente = st.sidebar.checkbox("Apenas com Receita Crescente", value=False, help=METRICS_HELP["Receita Sobe?"])

# --- SELEÇÃO DE ATIVOS ---
tickers_selecionados = st.multiselect(
    "Selecione os ativos para comparar", 
    TICKERS_COMUNS, 
    default=["PETR4.SA", "VALE3.SA", "AAPL", "MSFT"]
)

outros_tickers = st.text_input("Ou digite outros tickers separados por vírgula (Ex: TSLA, GOOGL, ITUB4.SA)")

if st.button("🚀 Buscar/Atualizar Dados do Mercado"):
    lista_final = list(tickers_selecionados)
    if outros_tickers:
        lista_final.extend([t.strip().upper() for t in outros_tickers.split(",") if t.strip()])
    
    if not lista_final:
        st.warning("Selecione ou digite ao menos um ticker.")
    else:
        with st.spinner("Consultando Yahoo Finance..."):
            dados_comp = get_asset_metrics(lista_final)
            st.session_state.raw_df_comp = pd.DataFrame(dados_comp)
            st.success("Dados carregados! Agora use os filtros na esquerda para analisar.")

# --- LÓGICA DE FILTRAGEM REATIVA ---
if "raw_df_comp" in st.session_state:
    df_filtered = st.session_state.raw_df_comp.copy()
    
    def filter_ipo_year(date_str):
        if pd.isna(date_str) or date_str == "N/A":
            return True
        try:
            year = int(str(date_str).split('-')[0])
            return ano_ipo[0] <= year <= ano_ipo[1]
        except:
            return True
            
    df_filtered = df_filtered[df_filtered["Data IPO"].apply(filter_ipo_year)]
    df_filtered = df_filtered[(df_filtered["P/L (P/E)"].isna()) | (df_filtered["P/L (P/E)"] <= pl_max)]
    df_filtered = df_filtered[(df_filtered["P/VP (P/B)"].isna()) | (df_filtered["P/VP (P/B)"] <= pvp_max)]
    df_filtered = df_filtered[(df_filtered["Div. Yield (%)"].isna()) | (df_filtered["Div. Yield (%)"] >= min_dividend)]
    df_filtered = df_filtered[(df_filtered["ROE (%)"].isna()) | (df_filtered["ROE (%)"] >= min_roe)]
    df_filtered = df_filtered[(df_filtered["ROIC (%)"].isna()) | (df_filtered["ROIC (%)"] >= min_roic)]
    
    if min_mcap_b > 0:
        min_mcap_raw = min_mcap_b * 1e9
        df_filtered = df_filtered[(df_filtered["Market Cap"].isna()) | (df_filtered["Market Cap"] >= min_mcap_raw)]
        
    if lucro_apenas:
        df_filtered = df_filtered[df_filtered["Lucro >0 (4A)?"] == "Sim"]
    if receita_crescente:
        df_filtered = df_filtered[df_filtered["Receita Sobe?"] == "Sim"]

    st.subheader(f"📊 Resultados Filtrados ({len(df_filtered)} ativos)")
    
    st.dataframe(
        df_filtered.style.format({
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
    
    if not df_filtered.empty:
        st.markdown("### ⭐ Adicionar aos Estudos")
        ticker_fav = st.selectbox("Escolha um ativo filtrado:", df_filtered["Ticker"].tolist())
        if st.button("Confirmar Favorito"):
            with Session(engine) as session:
                ativo = session.exec(select(Ativo).where(Ativo.ticker == ticker_fav)).first()
                if not ativo:
                    from finance import get_asset_basic_info
                    info = get_asset_basic_info(ticker_fav)
                    ativo = Ativo(ticker=ticker_fav, nome=info["nome"], tipo=info["tipo"], favorito=True)
                    session.add(ativo)
                else:
                    ativo.favorito = True
                    session.add(ativo)
                session.commit()
                st.success(f"{ticker_fav} pronto para estudos na aba da Carteira!")

    if not df_filtered.empty:
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Valuation: P/L (P/E)")
            df_v = df_filtered[df_filtered["P/L (P/E)"].notnull()]
            if not df_v.empty:
                fig = px.bar(df_v, x="Ticker", y="P/L (P/E)", color="Ticker", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Rentabilidade: ROE (%)")
            df_v = df_filtered[df_filtered["ROE (%)"].notnull()]
            if not df_v.empty:
                fig = px.bar(df_v, x="Ticker", y="ROE (%)", color="Ticker", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Eficiência: ROIC (%)")
            df_v = df_filtered[df_filtered["ROIC (%)"].notnull()]
            if not df_v.empty:
                fig = px.bar(df_v, x="Ticker", y="ROIC (%)", color="Ticker", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
        with c4:
            st.subheader("Patrimônio: P/VP (P/B)")
            df_v = df_filtered[df_filtered["P/VP (P/B)"].notnull()]
            if not df_v.empty:
                fig = px.bar(df_v, x="Ticker", y="P/VP (P/B)", color="Ticker", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

    # --- SIMULADOR DE INVESTIMENTO HISTÓRICO ---
    if not df_filtered.empty:
        st.markdown("---")
        st.header("🕰️ Simulador de Investimento Histórico")
        st.write("Descubra quanto você teria hoje se tivesse investido no passado nas empresas filtradas acima.")
        
        import yfinance as yf
        
        col_sim1, col_sim2 = st.columns(2)
        with col_sim1:
            sim_valor = st.number_input("Se eu tivesse investido (R$):", min_value=1.0, value=100.0, step=50.0)
        with col_sim2:
            sim_anos = st.number_input("Há quantos anos?", min_value=1, max_value=30, value=1, step=1)
            
        if st.button("Simular Retorno Histórico"):
            with st.spinner("Calculando a máquina do tempo dos investimentos..."):
                sim_resultados = []
                hoje = datetime.datetime.now()
                data_passado = hoje - datetime.timedelta(days=sim_anos * 365.25)
                
                for ticker in df_filtered["Ticker"].tolist():
                    try:
                        t = yf.Ticker(ticker)
                        start_date = (data_passado - datetime.timedelta(days=5)).strftime('%Y-%m-%d')
                        end_date = (data_passado + datetime.timedelta(days=5)).strftime('%Y-%m-%d')
                        hist = t.history(start=start_date, end=end_date)
                        if not hist.empty:
                            preco_passado = hist['Close'].iloc[0]
                            preco_atual_sim = t.fast_info['lastPrice']
                            qtd_comprada = sim_valor / preco_passado
                            valor_hoje = qtd_comprada * preco_atual_sim
                            rentab_sim = ((valor_hoje / sim_valor) - 1) * 100
                            sim_resultados.append({
                                "Ticker": ticker, "Preço Pago (R$)": preco_passado,
                                "Preço Atual (R$)": preco_atual_sim, "Valor Hoje (R$)": valor_hoje,
                                "Rentabilidade (%)": rentab_sim
                            })
                    except:
                        pass
                
                if sim_resultados:
                    df_sim = pd.DataFrame(sim_resultados).sort_values(by="Valor Hoje (R$)", ascending=False)
                    st.subheader(f"Resultado do Investimento (R$ {sim_valor} há {sim_anos} ano(s))")
                    st.dataframe(df_sim.style.format({"Preço Pago (R$)": "R$ {:.2f}", "Preço Atual (R$)": "R$ {:.2f}", "Valor Hoje (R$)": "R$ {:.2f}", "Rentabilidade (%)": "{:.2f}%"}).background_gradient(subset=["Rentabilidade (%)", "Valor Hoje (R$)"], cmap="RdYlGn"), use_container_width=True)
                    fig_sim = px.bar(df_sim, x="Ticker", y="Valor Hoje (R$)", color="Rentabilidade (%)", color_continuous_scale="RdYlGn", title=f"Evolução Patrimonial: R$ {sim_valor} -> Valor Atual")
                    fig_sim.add_hline(y=sim_valor, line_dash="dash", line_color="white", annotation_text="Capital Investido")
                    st.plotly_chart(fig_sim, use_container_width=True)

# --- SCREENER / EXPORTAÇÃO EM MASSA ---
st.markdown("---")
with st.expander("📥 Screener - Exportar Dados em Massa (CSV)", expanded=False):
    st.write("Baixe dados fundamentalistas de centenas de ativos para filtrar no Excel ou Google Sheets.")
    
    modo_export = st.radio("Escolha o lote para exportação:", 
                           ["Top 50 Ativos (Mais Rápido)", 
                            "Brasil - IBOVESPA (~80 ativos)", 
                            "EUA - S&P 500 Top 50", 
                            "TODOS os ativos (~130 ativos)"])
    
    if st.button("🔨 Gerar Arquivo para Download"):
        if "Top 50" in modo_export:
            lista_export = ALL_SCREENER_TICKERS[:50]
        elif "Brasil" in modo_export:
            lista_export = TICKERS_IBOVESPA
        elif "EUA" in modo_export:
            lista_export = TICKERS_SP500_TOP
        else:
            lista_export = ALL_SCREENER_TICKERS

        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_results = []
        batch_size = 10
        
        for i in range(0, len(lista_export), batch_size):
            batch = lista_export[i:i+batch_size]
            status_text.text(f"Processando ativos {i+1} a {min(i+batch_size, len(lista_export))} de {len(lista_export)}...")
            res = get_asset_metrics(batch)
            all_results.extend(res)
            progress_bar.progress(min((i + batch_size) / len(lista_export), 1.0))
        
        df_export = pd.DataFrame(all_results)
        csv = df_export.to_csv(index=False).encode('utf-8-sig')
        status_text.success(f"✅ Arquivo gerado com {len(df_export)} ativos!")
        st.download_button(
            label="📥 Baixar Dados em CSV",
            data=csv,
            file_name=f"investsmart_screener_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

st.sidebar.caption("v0.4.3 - InvestSmart AI Edition")
