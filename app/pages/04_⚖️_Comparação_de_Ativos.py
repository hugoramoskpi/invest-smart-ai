import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
import subprocess
from finance import get_asset_metrics, METRICS_HELP
from database import engine, Ativo
from sqlmodel import Session, select
from style import apply_global_style
from screener_tickers import get_all_market_tickers

st.set_page_config(page_title="Comparação de Ativos - InvestSmart", layout="wide", page_icon="⚖️")

# Aplica o Estilo Unificado
apply_global_style()

st.title("⚖️ Comparação e Screener de Ativos")
st.write("Compare ativos em tempo real ou filtre o mercado total (4000+ ativos) usando a base local.")

# --- SELETOR DE MODO ---
modo_analise = st.radio("Selecione o Modo de Análise:", 
                        ["🔍 Tempo Real (Ativos Específicos)", "🌍 Screener Global (Mercado Total BR + EUA)"],
                        horizontal=True)

# --- CONFIGURAÇÃO DOS FILTROS DINÂMICOS (SIDEBAR) ---
st.sidebar.header("🔍 Filtros de Análise")

current_year = datetime.datetime.now().year
ano_ipo = st.sidebar.slider("Janela Data de IPO", 1800, current_year, (1800, current_year), help=METRICS_HELP["Data IPO"])

pl_max = st.sidebar.slider("P/L (P/E) Máximo", -50.0, 200.0, 200.0, help=METRICS_HELP["P/L (P/E)"])
pvp_max = st.sidebar.slider("P/VP (P/B) Máximo", -10.0, 100.0, 100.0, help=METRICS_HELP["P/VP (P/B)"])
min_roic = st.sidebar.slider("ROIC Mínimo (%)", -50.0, 150.0, -50.0, help=METRICS_HELP["ROIC (%)"])
min_roe = st.sidebar.slider("ROE Mínimo (%)", -50.0, 150.0, -50.0, help=METRICS_HELP["ROE (%)"])
min_dividend = st.sidebar.slider("Div. Yield Mínimo (%)", 0.0, 50.0, 0.0, help=METRICS_HELP["Div. Yield (%)"])
min_mcap_b = st.sidebar.number_input("Market Cap Mín. (Bilhões)", min_value=0.0, value=0.0, help=METRICS_HELP["Market Cap"])

lucro_apenas = st.sidebar.checkbox("Empresas com Lucro (4A)", value=False)
receita_crescente = st.sidebar.checkbox("Receita Crescente", value=False)

# Função de filtragem reativa
def apply_filters(df):
    if df is None or df.empty:
        return pd.DataFrame()
    
    df_f = df.copy()
    
    # IPO Year
    def get_year(val):
        try: return int(str(val).split('-')[0])
        except: return 0
    df_f["ipo_year"] = df_f["Data IPO"].apply(get_year)
    df_f = df_f[(df_f["ipo_year"] == 0) | ((df_f["ipo_year"] >= ano_ipo[0]) & (df_f["ipo_year"] <= ano_ipo[1]))]
    
    # Métricas
    df_f = df_f[(df_f["P/L (P/E)"].isna()) | (df_f["P/L (P/E)"] <= pl_max)]
    df_f = df_f[(df_f["P/VP (P/B)"].isna()) | (df_f["P/VP (P/B)"] <= pvp_max)]
    df_f = df_f[(df_f["Div. Yield (%)"].isna()) | (df_f["Div. Yield (%)"] >= min_dividend)]
    df_f = df_f[(df_f["ROE (%)"].isna()) | (df_f["ROE (%)"] >= min_roe)]
    df_f = df_f[(df_f["ROIC (%)"].isna()) | (df_f["ROIC (%)"] >= min_roic)]
    
    if min_mcap_b > 0:
        df_f = df_f[(df_f["Market Cap"].isna()) | (df_f["Market Cap"] >= min_mcap_b * 1e9)]
        
    if lucro_apenas:
        df_f = df_f[df_f["Lucro >0 (4A)?"] == "Sim"]
    if receita_crescente:
        df_f = df_f[df_f["Receita Sobe?"] == "Sim"]
        
    return df_f

if modo_analise == "🔍 Tempo Real (Ativos Específicos)":
    # Lógica original de busca específica
    TICKERS_COMUNS = ["PETR4.SA", "VALE3.SA", "AAPL", "MSFT", "GOOGL", "AMZN", "BTC-USD"]
    sel_tickers = st.multiselect("Selecione ativos:", TICKERS_COMUNS, default=["PETR4.SA", "AAPL"])
    extra_tickers = st.text_input("Outros tickers (virgula):")
    
    if st.button("🚀 Buscar Dados Atuais"):
        lista = list(sel_tickers)
        if extra_tickers:
            lista.extend([t.strip().upper() for t in extra_tickers.split(",") if t.strip()])
        if lista:
            with st.spinner("Buscando no Yahoo Finance..."):
                st.session_state.df_tempo_real = pd.DataFrame(get_asset_metrics(lista))

    if "df_tempo_real" in st.session_state:
        df_res = apply_filters(st.session_state.df_tempo_real)
        st.subheader(f"📊 Resultados ({len(df_res)} ativos)")
        st.dataframe(df_res.style.format({"Preço Atual": "R$ {:.2f}", "P/L (P/E)": "{:.2f}", "P/VP (P/B)": "{:.2f}", "Div. Yield (%)": "{:.2f}%", "Market Cap": lambda x: f"B$ {x/1e9:.2f}B" if pd.notnull(x) else "N/A", "ROE (%)": "{:.2f}%", "ROIC (%)": "{:.2f}%"}), column_config={k: st.column_config.Column(help=v) for k, v in METRICS_HELP.items()}, use_container_width=True)

else:
    # MODO SCREENER GLOBAL
    DB_FILE = "market_database.csv"
    
    st.subheader("🌍 Screener Global (Mercado Total)")
    st.info("Este modo permite filtrar milhares de ativos instantaneamente usando a base local sincronizada.")
    
    if not os.path.exists(DB_FILE):
        st.warning("⚠️ Base de dados local não encontrada!")
        if st.button("🔨 Gerar Base de Dados Inicial (Isso pode demorar bastante)"):
            with st.spinner("Iniciando sincronização massiva..."):
                # Roda o script de sincronização como um processo separado para não travar o streamlit
                subprocess.Popen(["python", "sync_market_db.py"])
                st.info("Sincronização iniciada em segundo plano! Acompanhe o progresso no terminal. O arquivo aparecerá aqui quando pronto.")
    else:
        # Carrega a base local
        if "df_global" not in st.session_state:
            st.session_state.df_global = pd.read_csv(DB_FILE)
            
        st.write(f"✅ Base carregada com **{len(st.session_state.df_global)}** ativos (VTI/Russell 3000 + B3).")
        
        if st.button("🔄 Atualizar Base de Dados"):
             subprocess.Popen(["python", "sync_market_db.py"])
             st.success("Atualização iniciada em segundo plano!")

        df_res = apply_filters(st.session_state.df_global)
        st.subheader(f"🎯 Filtro Global: {len(df_res)} ativos encontrados")
        
        # Busca por nome ou ticker dentro do Screener
        search_query = st.text_input("Filtrar por Ticker ou Nome dentro do Screener:", "").upper()
        if search_query:
            df_res = df_res[df_res["Ticker"].str.contains(search_query) | df_res["Nome"].str.upper().str.contains(search_query)]

        st.dataframe(df_res.style.format({"Preço Atual": "{:.2f}", "P/L (P/E)": "{:.2f}", "P/VP (P/B)": "{:.2f}", "Div. Yield (%)": "{:.2f}%", "Market Cap": lambda x: f"B$ {x/1e9:.2f}B" if pd.notnull(x) else "N/A", "ROE (%)": "{:.2f}%", "ROIC (%)": "{:.2f}%"}), column_config={k: st.column_config.Column(help=v) for k, v in METRICS_HELP.items()}, use_container_width=True)

st.sidebar.caption("v0.5.0 - InvestSmart Enterprise Edition")
