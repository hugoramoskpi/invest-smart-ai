import streamlit as st
import pandas as pd
from database import engine, Ativo, Transacao, MetaAlocacao
from sqlmodel import Session, select
from finance import calculate_portfolio_performance, get_current_price, METRICS_HELP
from style import apply_global_style

st.set_page_config(page_title="Onde Aportar - InvestSmart", layout="wide", page_icon="💡")

# Aplica o Estilo Unificado
apply_global_style()

st.header("💡 Inteligência de Aporte e Rebalanceamento")
st.write("Defina suas metas e descubra onde investir para manter o equilíbrio da carteira.")

with Session(engine) as session:
    ativos_db = session.exec(select(Ativo)).all()
    
    # 1. Definição de Metas
    with st.expander("⚙️ Configurar Metas de Alocação", expanded=False):
        st.subheader("Metas por Classe de Ativo")
        classes = ["Ações", "Stocks", "ETFs", "FIIs", "Cripto", "REITs"]
        cols = st.columns(3)
        for i, cls in enumerate(classes):
            with cols[i % 3]:
                meta_cls = session.exec(select(MetaAlocacao).where(MetaAlocacao.nome == cls)).first()
                val_atual = meta_cls.alvo_percentual if meta_cls else 0.0
                nova_meta = st.number_input(f"Meta {cls} (%)", 0.0, 100.0, float(val_atual), key=f"meta_{cls}")
                if nova_meta != val_atual:
                    if not meta_cls:
                        meta_cls = MetaAlocacao(nome=cls, alvo_percentual=nova_meta, categoria="Classe")
                    else:
                        meta_cls.alvo_percentual = nova_meta
                    session.add(meta_cls)
                    session.commit()

        st.subheader("Metas por Ativo (Dentro da Classe)")
        for a in ativos_db:
            meta_a = session.exec(select(MetaAlocacao).where(MetaAlocacao.nome == a.ticker)).first()
            val_a = meta_a.alvo_percentual if meta_a else 0.0
            nova_meta_a = st.number_input(f"Meta {a.ticker} (%)", 0.0, 100.0, float(val_a), key=f"meta_{a.ticker}")
            if nova_meta_a != val_a:
                if not meta_a:
                    meta_a = MetaAlocacao(nome=a.ticker, alvo_percentual=nova_meta_a, categoria="Ativo")
                else:
                    meta_a.alvo_percentual = nova_meta_a
                session.add(meta_a)
                session.commit()

    # 2. Cálculo de Rebalanceamento
    dados_carteira = []
    for a in ativos_db:
        transacoes = session.exec(select(Transacao).where(Transacao.ativo_id == a.id)).all()
        if transacoes:
            qtd = sum(t.quantidade for t in transacoes if t.tipo_transacao == "Compra") - sum(t.quantidade for t in transacoes if t.tipo_transacao == "Venda")
            if qtd > 0:
                dados_carteira.append({"ticker": a.ticker, "transacoes": transacoes, "tipo": a.tipo})

    if not dados_carteira:
        st.info("Sua carteira está vazia. Registre operações para calcular o rebalanceamento.")
    else:
        perf_data, total_inv, total_at = calculate_portfolio_performance(dados_carteira)
        df = pd.DataFrame(perf_data)
        
        # Merge com metas
        metas = session.exec(select(MetaAlocacao)).all()
        meta_dict = {m.nome: m.alvo_percentual for m in metas}
        
        df["Meta (%)"] = df["Ativo"].map(lambda x: meta_dict.get(x, 0.0))
        df["Atual (%)"] = (df["Valor Atual"] / total_at) * 100
        df["Diferença (%)"] = df["Meta (%)"] - df["Atual (%)"]
        
        st.subheader("📊 Situação Atual vs Meta")
        st.dataframe(
            df[["Ativo", "Valor Atual", "Atual (%)", "Meta (%)", "Diferença (%)"]].style.format({
                "Valor Atual": "R$ {:.2f}",
                "Atual (%)": "{:.2f}%",
                "Meta (%)": "{:.2f}%",
                "Diferença (%)": "{:.2f}%"
            }).background_gradient(subset=["Diferença (%)"], cmap="RdYlGn"), 
            column_config={
                "Valor Atual": st.column_config.Column(help=METRICS_HELP["Valor de Mercado"]),
                "Atual (%)": st.column_config.Column(help="Porcentagem atual do ativo na sua carteira real."),
                "Meta (%)": st.column_config.Column(help="Porcentagem que você definiu como objetivo para este ativo."),
                "Diferença (%)": st.column_config.Column(help="Quanto o ativo está abaixo (positivo) ou acima (negativo) da meta.")
            },
            use_container_width=True
        )

        # 3. Sugestão de Aporte
        st.markdown("---")
        st.subheader("💰 Sugestão de Aporte")
        valor_aporte = st.number_input("Quanto você deseja aportar hoje? (R$)", 0.0, 1000000.0, 500.0)
        
        if valor_aporte > 0:
            # Lógica: Aportar nos ativos que estão com maior "Diferença (%)" positiva (ficou para trás)
            df_sugestao = df[df["Diferença (%)"] > 0].sort_values(by="Diferença (%)", ascending=False)
            
            if df_sugestao.empty:
                st.success("Sua carteira está perfeitamente balanceada ou todos os ativos superaram a meta!")
            else:
                st.write(f"Para rebalancear com R$ {valor_aporte:.2f}, foque nos seguintes ativos:")
                
                # Distribuição simples proporcional à diferença
                total_diff = df_sugestao["Diferença (%)"].sum()
                df_sugestao["Valor a Aportar"] = (df_sugestao["Diferença (%)"] / total_diff) * valor_aporte
                
                for _, row in df_sugestao.iterrows():
                    st.info(f"**{row['Ativo']}**: Sugestão de aporte de **R$ {row['Valor a Aportar']:.2f}**")

st.sidebar.caption("v0.4.3 - InvestSmart AI Edition")
