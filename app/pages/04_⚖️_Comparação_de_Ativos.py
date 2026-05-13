import streamlit as st
import pandas as pd
import plotly.express as px
from finance import get_asset_metrics
from database import engine, Ativo
from sqlmodel import Session, select

st.set_page_config(page_title="Comparação de Ativos - InvestSmart", layout="wide")

st.header("⚖️ Comparação de Ativos (Brasil e EUA)")
st.write("Compare métricas fundamentalistas e filtre os melhores ativos.")

TICKERS_COMUNS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA", "MGLU3.SA", "BBAS3.SA",
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX",
    "IVVB11.SA", "BOVA11.SA", "SMAL11.SA"
]

# Configuração de Filtros na Sidebar
st.sidebar.header("🔍 Filtros de Busca")
min_roic = st.sidebar.slider("ROIC Mínimo (%)", -50, 100, -50)
min_dividend = st.sidebar.slider("Div. Yield Mínimo (%)", 0, 30, 0)
lucro_apenas = st.sidebar.checkbox("Apenas empresas com Lucro (4A)", value=False)
receita_crescente = st.sidebar.checkbox("Apenas com Receita Crescente", value=False)

tickers_selecionados = st.multiselect(
    "Selecione os ativos para comparar", 
    TICKERS_COMUNS, 
    default=["PETR4.SA", "VALE3.SA", "AAPL", "MSFT"]
)

outros_tickers = st.text_input("Ou digite outros tickers separados por vírgula (Ex: TSLA, GOOGL, ITUB4.SA)")

col_btn1, col_btn2 = st.columns([1, 4])

executar = col_btn1.button("Executar Comparação")

if executar:
    lista_final = list(tickers_selecionados)
    if outros_tickers:
        lista_final.extend([t.strip().upper() for t in outros_tickers.split(",") if t.strip()])
    
    if not lista_final:
        st.warning("Selecione ou digite ao menos um ticker.")
    else:
        st.session_state.last_comparison = lista_final
        with st.spinner("Buscando dados no Yahoo Finance..."):
            dados_comp = get_asset_metrics(lista_final)
            df_comp = pd.DataFrame(dados_comp)
            
            # Aplicando Filtros
            def parse_pct(val):
                try:
                    return float(str(val).replace('%', ''))
                except:
                    return -999.0
            
            if "ROIC" in df_comp.columns:
                df_comp["roic_num"] = df_comp["ROIC"].apply(parse_pct)
                df_comp = df_comp[df_comp["roic_num"] >= min_roic]
            
            if "Div. Yield (%)" in df_comp.columns:
                df_comp = df_comp[(df_comp["Div. Yield (%)"] == "N/A") | (df_comp["Div. Yield (%)"] >= min_dividend)]
            
            if lucro_apenas:
                df_comp = df_comp[df_comp["Lucro >0 (4A)?"] == "Sim"]
                
            if receita_crescente:
                df_comp = df_comp[df_comp["Receita Sobe?"] == "Sim"]

            st.session_state.df_comp = df_comp

if "df_comp" in st.session_state:
    df_comp = st.session_state.df_comp
    
    # Limpeza visual
    df_display = df_comp.drop(columns=["roic_num"], errors="ignore")
    
    st.subheader("Resultados da Comparação")
    st.dataframe(df_display, use_container_width=True)
    
    # Opção de Favoritar (Adicionar aos Estudos)
    st.markdown("### ⭐ Favoritar para Estudos")
    ticker_to_fav = st.selectbox("Escolha um ativo para favoritar:", df_comp["Ticker"].tolist())
    if st.button("Adicionar aos Estudos"):
        with Session(engine) as session:
            ativo = session.exec(select(Ativo).where(Ativo.ticker == ticker_to_fav)).first()
            if not ativo:
                # Busca info básica para criar o ativo
                from finance import get_asset_basic_info
                info = get_asset_basic_info(ticker_to_fav)
                ativo = Ativo(ticker=ticker_to_fav, nome=info["nome"], tipo=info["tipo"], favorito=True)
                session.add(ativo)
            else:
                ativo.favorito = True
                session.add(ativo)
            session.commit()
            st.success(f"{ticker_to_fav} adicionado à sua lista de estudos!")

    if df_comp.empty:
        st.info("Nenhum ativo corresponde aos filtros selecionados.")
    else:
        # Gráficos
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Comparativo: P/L (P/E Ratio)")
            df_valid_pl = df_comp[df_comp["P/L (P/E)"] != "N/A"]
            if not df_valid_pl.empty:
                fig_pl = px.bar(df_valid_pl, x="Ticker", y="P/L (P/E)", color="Ticker", template="plotly_white")
                st.plotly_chart(fig_pl, use_container_width=True)
        with c2:
            st.subheader("Comparativo: ROE (%)")
            df_valid_roe = df_comp[df_comp["ROE (%)"] != "N/A"]
            if not df_valid_roe.empty:
                fig_roe = px.bar(df_valid_roe, x="Ticker", y="ROE (%)", color="Ticker", template="plotly_white")
                st.plotly_chart(fig_roe, use_container_width=True)
        
        c3, c4 = st.columns(2)
        with c3:
            st.subheader("Eficiência: ROIC")
            df_valid_roic = df_comp[df_comp["ROIC"] != "N/A"]
            if not df_valid_roic.empty:
                # Usa a coluna numérica que já tratamos ou recria
                df_valid_roic["ROIC_val"] = df_valid_roic["ROIC"].str.replace('%','').astype(float)
                fig_roic = px.bar(df_valid_roic, x="Ticker", y="ROIC_val", color="Ticker", labels={"ROIC_val": "ROIC (%)"})
                st.plotly_chart(fig_roic, use_container_width=True)
        with c4:
            st.subheader("Preço / Valor Patrimonial (P/VP)")
            df_valid_pvp = df_comp[df_comp["P/VP (P/B)"] != "N/A"]
            if not df_valid_pvp.empty:
                fig_pvp = px.bar(df_valid_pvp, x="Ticker", y="P/VP (P/B)", color="Ticker")
                st.plotly_chart(fig_pvp, use_container_width=True)
