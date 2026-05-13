import pandas as pd
import requests

def get_ibovespa_tickers():
    """Busca tickers das ações brasileiras listadas na B3."""
    try:
        url = 'https://pt.wikipedia.org/wiki/Lista_de_companhias_citadas_no_Ibovespa'
        tables = pd.read_html(url)
        for table in tables:
            if 'Código' in table.columns:
                tickers = table['Código'].astype(str) + ".SA"
                return tickers.tolist()
    except Exception as e:
        print(f"Erro ao buscar IBOVESPA: {e}")
    
    return ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA"]

def get_us_tickers():
    """Busca uma lista massiva de ações americanas (referência VTI)."""
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt"
        response = requests.get(url)
        if response.status_code == 200:
            tickers = response.text.splitlines()
            return [t.strip().upper() for t in tickers if t.strip()]
    except Exception as e:
        print(f"Erro ao buscar tickers EUA: {e}")
    
    return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA"]

def get_global_vea_vwo_tickers():
    """
    Retorna os principais componentes internacionais dos ETFs VEA e VWO (Top Holdings).
    Estes ativos representam mercados desenvolvidos (ex-US) e emergentes.
    """
    return [
        # Developed Markets (VEA components - Top ADRs)
        "ASML", "NVO", "NVS", "SHEL", "AZN", "TM", "TTE", "HSBC", "SAP", "BHP", 
        "SNY", "RIO", "DEO", "UL", "GSK", "ABB", "RELX", "HMC", "HDB", "IBN",
        # Emerging Markets (VWO components - Top ADRs)
        "TSM", "BABA", "PDD", "JD", "BIDU", "NTES", "MELI", "VALE", "PBR", "NU",
        "ITUB", "BBD", "GGB", "CPNG", "AMX", "FMX", "TCEHY", "KEP", "HDFC"
    ]

def get_all_market_tickers():
    br = get_ibovespa_tickers()
    us = get_us_tickers()
    global_assets = get_global_vea_vwo_tickers()
    return list(set(br + us + global_assets))
