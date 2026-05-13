import pandas as pd
import requests

def get_ibovespa_tickers():
    """Busca tickers das ações brasileiras listadas na B3."""
    try:
        url = 'https://pt.wikipedia.org/wiki/Lista_de_companhias_citadas_no_Ibovespa'
        # Adiciona header para evitar 403 Forbidden
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        tables = pd.read_html(response.text)
        for table in tables:
            if 'Código' in table.columns:
                tickers = table['Código'].astype(str) + ".SA"
                return tickers.tolist()
    except Exception as e:
        print(f"Erro ao buscar IBOVESPA: {e}")
    
    return [
        "RRRP3.SA", "ALOS3.SA", "ALPA3.SA", "ABEV3.SA", "ARZZ3.SA", "ASAI3.SA", "AZUL4.SA", "B3SA3.SA", "BBSE3.SA", "BBDC3.SA",
        "BBDC4.SA", "BRAP4.SA", "BBAS3.SA", "BRKM5.SA", "BRFS3.SA", "BPAC11.SA", "CRFB3.SA", "CCRO3.SA", "CMIG4.SA", "CIEL3.SA",
        "COGN3.SA", "CPLE6.SA", "CSAN3.SA", "CPFE6.SA", "CMIN3.SA", "CVCB4.SA", "CYRE3.SA", "DXCO3.SA", "ELET3.SA", "ELET6.SA",
        "EMBR3.SA", "ENGI11.SA", "ENEV11.SA", "EGIE3.SA", "EQTL3.SA", "EZTC3.SA", "FLRY3.SA", "GGBR4.SA", "GOAU4.SA", "NTCO3.SA",
        "SOMA3.SA", "HAPV3.SA", "HYPE3.SA", "IGTI11.SA", "IRBR3.SA", "ITSA4.SA", "ITUB4.SA", "JBSS3.SA", "KLBN11.SA", "RENT3.SA",
        "LREN3.SA", "LWSA3.SA", "MGLU3.SA", "MRFG3.SA", "CASH3.SA", "BEEF3.SA", "MRVE3.SA", "MULT3.SA", "PCAR3.SA", "PETR3.SA",
        "PETR4.SA", "PRIO3.SA", "PETZ3.SA", "RADL3.SA", "RAIZ4.SA", "RDOR3.SA", "RAIL3.SA", "SBSP3.SA", "SANB11.SA", "SMTO3.SA",
        "CSNA3.SA", "SLCE3.SA", "SUZB3.SA", "TAEE11.SA", "VIVT11.SA", "TIMS3.SA", "TOTS3.SA", "UGPA3.SA", "USIM5.SA", "VALE3.SA",
        "VIIA3.SA", "VBBR3.SA", "WEGE3.SA", "YDUQ3.SA"
    ]

def get_us_tickers():
    """Busca uma lista massiva de ações americanas (NASDAQ + NYSE)."""
    all_us = []
    try:
        # NASDAQ
        r1 = requests.get('https://raw.githubusercontent.com/abbadata/stock-tickers/main/data/nasdaqsymbols.txt')
        if r1.status_code == 200:
            all_us.extend(r1.text.splitlines())
        
        # NYSE
        r2 = requests.get('https://raw.githubusercontent.com/abbadata/stock-tickers/main/data/nysesymbols.txt')
        if r2.status_code == 200:
            all_us.extend(r2.text.splitlines())
            
        return [t.strip().upper() for t in all_us if t.strip()]
    except Exception as e:
        print(f"Erro ao buscar tickers EUA: {e}")
    
    return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA"]

def get_global_vea_vwo_tickers():
    """Retorna os principais componentes internacionais."""
    return [
        "ASML", "NVO", "NVS", "SHEL", "AZN", "TM", "TTE", "HSBC", "SAP", "BHP", 
        "SNY", "RIO", "DEO", "UL", "GSK", "ABB", "RELX", "HMC", "HDB", "IBN",
        "TSM", "BABA", "PDD", "JD", "BIDU", "NTES", "MELI", "VALE", "PBR", "NU",
        "ITUB", "BBD", "GGB", "CPNG", "AMX", "FMX", "TCEHY", "KEP", "HDFC"
    ]

def get_all_market_tickers():
    br = get_ibovespa_tickers()
    us = get_us_tickers()
    global_assets = get_global_vea_vwo_tickers()
    # Remove duplicatas e garante que são strings limpas
    return sorted(list(set(str(t).strip().upper() for t in (br + us + global_assets) if t)))
