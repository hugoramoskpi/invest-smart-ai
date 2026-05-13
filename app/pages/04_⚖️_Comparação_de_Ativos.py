import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
import concurrent.futures
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
                        ["🔍 Tempo Real (Ativos Específicos)", "🌍 Screener Global (Mercado Total BR + EUA + Global)"],
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

# Filtro de País (Sidebar)
if "df_global" in st.session_state or "df_tempo_real" in st.session_state:
    df_ref = st.session_state.get("df_global") if modo_analise != "🔍 Tempo Real (Ativos Específicos)" else st.session_state.get("df_tempo_real")
    if df_ref is not None and "País" in df_ref.columns:
        paises_disponiveis = sorted(df_ref["País"].dropna().unique().tolist())
        filtro_paises = st.sidebar.multiselect("Filtrar por País:", paises_disponiveis, default=None)
    else:
        filtro_paises = []
else:
    filtro_paises = []

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
    
    # País
    if filtro_paises:
        df_f = df_f[df_f["País"].isin(filtro_paises)]
    
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

def safe_format(val, fmt="{:.2f}"):
    """Formata valor apenas se for numérico e não nulo."""
    if pd.isna(val) or val is None:
        return "N/A"
    try:
        return fmt.format(val)
    except:
        return str(val)

if modo_analise == "🔍 Tempo Real (Ativos Específicos)":
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
        
        # Formatação segura para evitar erro NoneType
        st.dataframe(
            df_res.style.format({
                "Preço Atual": lambda x: safe_format(x, "{:.2f}"),
                "P/L (P/E)": lambda x: safe_format(x, "{:.2f}"),
                "P/VP (P/B)": lambda x: safe_format(x, "{:.2f}"),
                "Div. Yield (%)": lambda x: safe_format(x, "{:.2f}%"),
                "Market Cap": lambda x: f"B$ {x/1e9:.2f}B" if pd.notnull(x) and x > 0 else "N/A",
                "ROE (%)": lambda x: safe_format(x, "{:.2f}%"),
                "ROIC (%)": lambda x: safe_format(x, "{:.2f}%")
            }, na_rep="N/A"), 
            column_config={k: st.column_config.Column(help=v) for k, v in METRICS_HELP.items()}, 
            use_container_width=True
        )

else:
    DB_FILE = "market_database.csv"
    st.subheader("🌍 Screener Global (Mercado Total)")
    st.write("Incluindo ativos do Brasil (IBOV), EUA (VTI) e Global (Top VEA/VWO).")
    
    def sync_inside_streamlit():
        tickers = get_all_market_tickers()
        total = len(tickers)
        batch_size = 25
        all_data = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_batch = {executor.submit(get_asset_metrics, tickers[i:i + batch_size]): i for i in range(0, total, batch_size)}
            processed = 0
            for future in concurrent.futures.as_completed(future_to_batch):
                try:
                    data = future.result()
                    all_data.extend(data)
                    processed += len(data)
                    progress_bar.progress(min(processed / total, 1.0))
                    status_text.text(f"🚀 Sincronizando: {processed}/{total} ativos...")
                except: pass

        df = pd.DataFrame(all_data)
        df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
        st.session_state.df_global = df
        status_text.success(f"✅ Base de dados atualizada ({len(df)} ativos)!")

    if not os.path.exists(DB_FILE):
        st.warning("⚠️ Base de dados local não encontrada!")
        if st.button("🔨 Gerar Base de Dados Inicial (Feedback Visual)"):
            sync_inside_streamlit()
    else:
        if "df_global" not in st.session_state:
            st.session_state.df_global = pd.read_csv(DB_FILE)
            
        st.write(f"✅ Base carregada com **{len(st.session_state.df_global)}** ativos.")
        if st.button("🔄 Atualizar Base de Dados"):
             sync_inside_streamlit()

        df_res = apply_filters(st.session_state.df_global)
        st.subheader(f"🎯 Filtro Global: {len(df_res)} ativos encontrados")
        
        search_query = st.text_input("Filtrar por Ticker ou Nome:", "").upper()
        if search_query:
            df_res = df_res[df_res["Ticker"].astype(str).str.contains(search_query) | df_res["Nome"].astype(str).str.upper().str.contains(search_query)]

        st.dataframe(
            df_res.style.format({
                "Preço Atual": lambda x: safe_format(x, "{:.2f}"),
                "P/L (P/E)": lambda x: safe_format(x, "{:.2f}"),
                "P/VP (P/B)": lambda x: safe_format(x, "{:.2f}"),
                "Div. Yield (%)": lambda x: safe_format(x, "{:.2f}%"),
                "Market Cap": lambda x: f"B$ {x/1e9:.2f}B" if pd.notnull(x) and x > 0 else "N/A",
                "ROE (%)": lambda x: safe_format(x, "{:.2f}%"),
                "ROIC (%)": lambda x: safe_format(x, "{:.2f}%")
            }, na_rep="N/A"), 
            column_config={k: st.column_config.Column(help=v) for k, v in METRICS_HELP.items()}, 
            use_container_width=True
        )

st.sidebar.caption("v0.5.3 - InvestSmart Global Edition")
