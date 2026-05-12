import streamlit as st
from database import create_db_and_tables
from seed import seed_db

# Inicializa o banco de dados e a base imaginária
create_db_and_tables()
seed_db()

st.set_page_config(
    page_title="InvestSmart",
    layout="wide",
    page_icon="🚀"
)

st.title("🚀 InvestSmart: Seu Controle Inteligente")

st.markdown("""
### Bem-vindo ao InvestSmart!
Seu hub completo para controle de investimentos e análise com Inteligência Artificial.

**Utilize o menu lateral para navegar entre as funcionalidades:**

*   **📊 Dashboard:** Visão geral da sua performance e alocação.
*   **💼 Minha Carteira:** Detalhamento de todos os seus ativos.
*   **📝 Registrar Operação:** Adicione novas compras e vendas.
*   **⚖️ Comparação de Ativos:** Analise métricas fundamentalistas (BR e EUA).
*   **🤖 Assistente IA:** Converse com nosso agente inteligente sobre seus investimentos.

---
*v0.3.0 - InvestSmart AI Edition*
""")

st.sidebar.success("Selecione uma página acima.")
st.sidebar.markdown("---")
st.sidebar.caption("Powered by Gemini CLI")
