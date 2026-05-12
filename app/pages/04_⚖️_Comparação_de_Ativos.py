import streamlit as st
import pandas as pd
import plotly.express as px
from finance import get_asset_metrics

st.set_page_config(page_title="Comparação de Ativos - InvestSmart", layout="wide")

st.header("⚖️ Comparação de Ativos (Brasil e EUA)")
st.write("Compare métricas fundamentalistas de diversas empresas simultaneamente.")

TICKERS_COMUNS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA", "MGLU3.SA", "BBAS3.SA",
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX",
    "IVVB11.SA", "BOVA11.SA", "SMAL11.SA"
]

tickers_selecionados = st.multiselect(
    "Selecione os ativos para comparar", 
    TICKERS_COMUNS, 
    default=["PETR4.SA", "VALE3.SA", "AAPL", "MSFT"]
)

outros_tickers = st.text_input("Ou digite outros tickers separados por vírgula (Ex: TSLA, GOOGL, ITUB4.SA)")

if st.button("Executar Comparação"):
    lista_final = list(tickers_selecionados)
    if outros_tickers:
        lista_final.extend([t.strip().upper() for t in outros_tickers.split(",") if t.strip()])
    
    if not lista_final:
        st.warning("Selecione ou digite ao menos um ticker.")
    else:
        with st.spinner("Buscando dados no Yahoo Finance..."):
            dados_comp = get_asset_metrics(lista_final)
            df_comp = pd.DataFrame(dados_comp)
            st.dataframe(df_comp, use_container_width=True)
            
            # Gráfico comparativo de P/L
            st.subheader("Comparativo Visual: P/L (P/E Ratio)")
            df_valid = df_comp[df_comp["P/L (P/E)"] != "N/A"]
            if not df_valid.empty:
                fig_pl = px.bar(df_valid, x="Ticker", y="P/L (P/E)", color="Ticker", title="Índice P/L por Ativo")
                st.plotly_chart(fig_pl, use_container_width=True)
