import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_current_price(ticker: str) -> float:
    """Busca o preço atual de um ativo via yfinance."""
    try:
        data = yf.Ticker(ticker)
        # Tenta pegar o preço de fechamento mais recente
        price = data.fast_info['lastPrice']
        return round(price, 2)
    except Exception as e:
        print(f"Erro ao buscar preço para {ticker}: {e}")
        return 0.0

def get_history(ticker: str, period: str = "1mo") -> pd.DataFrame:
    """Busca o histórico de preços para gerar gráficos."""
    try:
        data = yf.download(ticker, period=period)
        return data['Close']
    except Exception as e:
        print(f"Erro ao buscar histórico para {ticker}: {e}")
        return pd.DataFrame()

def get_asset_metrics(tickers: list) -> list:
    """Busca métricas detalhadas para a aba de comparação."""
    metrics = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            metrics.append({
                "Ticker": ticker,
                "Nome": info.get("shortName", "N/A"),
                "Setor": info.get("sector", "N/A"),
                "Preço Atual": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
                "P/L (P/E)": info.get("trailingPE", "N/A"),
                "P/VP (P/B)": info.get("priceToBook", "N/A"),
                "Div. Yield (%)": round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else "N/A",
                "Market Cap": info.get("marketCap", "N/A"),
                "ROE": info.get("returnOnEquity", "N/A"),
            })
        except Exception as e:
            metrics.append({
                "Ticker": ticker, "Nome": "Erro ao buscar dados", 
                "Setor": "-", "Preço Atual": "-", "P/L (P/E)": "-", 
                "P/VP (P/B)": "-", "Div. Yield (%)": "-", "Market Cap": "-", "ROE": "-"
            })
    return metrics

def calculate_portfolio_performance(ativos_transacoes):
    """
    Recebe uma lista de ativos e suas transações e calcula:
    - Custo Total
    - Valor Atual
    - Lucro/Prejuízo (P&L)
    """
    performance = []
    total_investido = 0
    total_atual = 0
    
    for item in ativos_transacoes:
        ticker = item['ticker']
        qtd_total = sum(t.quantidade for t in item['transacoes'] if t.tipo_transacao == "Compra")
        qtd_total -= sum(t.quantidade for t in item['transacoes'] if t.tipo_transacao == "Venda")
        
        if qtd_total <= 0:
            continue
            
        custo_medio = sum(t.preco * t.quantidade for t in item['transacoes'] if t.tipo_transacao == "Compra") / sum(t.quantidade for t in item['transacoes'] if t.tipo_transacao == "Compra")
        
        preco_atual = get_current_price(ticker)
        valor_atual = qtd_total * preco_atual
        custo_total = qtd_total * custo_medio
        
        lucro = valor_atual - custo_total
        rentabilidade = (lucro / custo_total) * 100 if custo_total > 0 else 0
        
        performance.append({
            "Ativo": ticker,
            "Qtd": qtd_total,
            "Custo Médio": round(custo_medio, 2),
            "Preço Atual": preco_atual,
            "Valor Atual": round(valor_atual, 2),
            "P&L": round(lucro, 2),
            "Rentab. (%)": round(rentabilidade, 2)
        })
        
        total_investido += custo_total
        total_atual += valor_atual
        
    return performance, total_investido, total_atual
