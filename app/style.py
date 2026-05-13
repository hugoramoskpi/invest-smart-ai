import streamlit as st

def apply_global_style():
    """Aplica o CSS customizado e o branding do menu lateral em todas as páginas."""
    
    st.markdown("""
        <style>
        /* Estilização do Menu Lateral */
        section[data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }
        
        section[data-testid="stSidebar"] .st-emotion-cache-16t9854 {
            color: #c9d1d9;
        }

        /* Melhora o espaçamento da navegação */
        [data-testid="stSidebarNav"] ul {
            padding-top: 1rem;
        }
        
        [data-testid="stSidebarNav"] li a span {
            font-weight: 500;
            font-size: 1.05rem;
        }

        /* Esconde o link 'main' redundante */
        [data-testid="stSidebarNav"] li:first-child {
            display: none;
        }

        /* Estilo dos Cards de Métrica */
        div[data-testid="stMetric"] {
            background-color: #0d1117;
            border: 1px solid #30363d;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            color: #58a6ff;
        }

        /* Botões principais */
        .stButton>button {
            border-radius: 8px;
            background-color: #238636;
            color: white;
            border: none;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #2ea043;
            transform: scale(1.02);
        }
        </style>
        """, unsafe_allow_html=True)

    # Título e Logo no Menu Lateral (Branding)
    st.sidebar.markdown("""
        <div style="text-align: center; padding-bottom: 20px;">
            <h1 style='color: #58a6ff; font-size: 2.2rem;'>🚀</h1>
            <h2 style='color: #c9d1d9; font-size: 1.2rem; margin-top: -10px;'>InvestSmart</h2>
            <p style='color: #8b949e; font-size: 0.8rem;'>Controle de Investimentos</p>
        </div>
        <hr style="margin: 10px 0; border-color: #30363d;">
        """, unsafe_allow_html=True)
