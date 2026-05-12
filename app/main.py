import streamlit as st
from database import create_db_and_tables
from seed import seed_db

# Inicializa banco
create_db_and_tables()
seed_db()

# Esta página 'main.py' é o ponto de entrada oficial que o sistema busca.
# No entanto, para exibir um ícone na Home no menu lateral,
# nós usamos o arquivo 'pages/00_🏠_Dashboard.py'.

# O código abaixo apenas redireciona visualmente ou exibe uma mensagem 
# caso o usuário caia no link direto do 'main' sem passar pelo menu.

st.set_page_config(page_title="InvestSmart", layout="wide")

# CSS para esconder o link 'main' redundante e focar no link com ícone
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] li:first-child {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

# Redireciona logicamente para a página do Dashboard com ícone
st.switch_page("pages/00_🏠_Dashboard.py")
