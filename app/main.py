import streamlit as st
import pandas as pd
import plotly.express as px
from database import engine, Ativo, Transacao, create_db_and_tables
from sqlmodel import Session, select
from finance import calculate_portfolio_performance
from seed import seed_db
from style import apply_global_style

# Inicializa banco e seed
create_db_and_tables()
seed_db()

# Esta página redireciona para a Home com ícone (00_🏠_Dashboard.py)
st.set_page_config(page_title="InvestSmart", layout="wide")

# Aplica o estilo global para evitar "piscadas" visuais antes do redirecionamento
apply_global_style()

# Redireciona para o Dashboard real
st.switch_page("pages/00_🏠_Dashboard.py")
