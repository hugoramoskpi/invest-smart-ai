import pandas as pd
import requests

def get_ibovespa_tickers():
    """Busca tickers das ações brasileiras listadas na B3."""
    try:
        # Usando uma lista mais ampla da Wikipédia para ativos do Brasil
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
    """
    Busca uma lista massiva de ações americanas (referência VTI).
    Usa um repositório confiável para obter ~4000 tickers (NYSE + NASDAQ).
    """
    try:
        # Repositório público com lista atualizada de tickers americanos
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all_tickers.txt"
        response = requests.get(url)
        if response.status_code == 200:
            tickers = response.text.splitlines()
            # Limpa tickers (remove nomes vazios e garante maiúsculas)
            return [t.strip().upper() for t in tickers if t.strip()]
    except Exception as e:
        print(f"Erro ao buscar tickers EUA: {e}")
    
    # Fallback: Top S&P 500
    return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA"]

def get_all_market_tickers():
    br = get_ibovespa_tickers()
    us = get_us_tickers()
    return list(set(br + us))
