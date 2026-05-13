import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

METRICS_HELP = {
    "Investimento Total": "Soma de todos os aportes realizados (Quantidade x Custo Médio).",
    "Valor de Mercado": "Valor atualizado da carteira baseado nas cotações mais recentes.",
    "Lucro/Prejuízo Absoluto": "Diferença financeira entre o Valor de Mercado e o Investimento Total.",
    "Qtd de Ativos": "Número de ativos diferentes atualmente na sua carteira.",
    "Preço Atual": "Última cotação de fechamento ou preço em tempo real do ativo.",
    "P/L (P/E)": "Preço sobre Lucro. Indica quantos anos levaria para reaver o capital investido com o lucro atual. Em geral, quanto menor, mais 'barata' está a empresa.",
    "P/VP (P/B)": "Preço sobre Valor Patrimonial. Compara o valor de mercado da empresa com seu patrimônio contábil.",
    "Div. Yield (%)": "Dividend Yield. Rentabilidade dos dividendos pagos nos últimos 12 meses em relação ao preço atual da ação.",
    "Market Cap": "Valor de Mercado total da empresa na bolsa (número de ações x preço).",
    "ROE (%)": "Return on Equity (Retorno sobre Patrimônio Líquido). Mede a capacidade da empresa de gerar lucro usando o dinheiro dos acionistas.",
    "ROIC (%)": "Return on Invested Capital. Mede a eficiência da gestão em gerar retornos sobre todo o capital investido na operação do negócio.",
    "Data IPO": "Data da oferta pública inicial (quando a empresa estreou na bolsa de valores).",
    "Lucro >0 (4A)?": "Verifica se a empresa reportou lucro líquido positivo consecutivamente em cada um dos últimos 4 anos fiscais.",
    "Receita Sobe?": "Verifica se a receita total da empresa cresceu consecutivamente ano após ano nos últimos 4 anos.",
    "Custo Médio": "Preço médio pago por unidade do ativo, ponderado por todas as compras.",
    "P&L": "Profit & Loss (Lucro ou Prejuízo) nominal deste ativo na sua carteira.",
    "Rentab. (%)": "Rentabilidade percentual total (Valor Atual / Custo Total) deste ativo.",
    "País": "País de sede e registro oficial da empresa."
}

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

def get_historical_price(ticker: str, date: str) -> float:
    """Busca o preço de fechamento na data informada (ou próximo dia útil)."""
    try:
        t = yf.Ticker(ticker)
        start_dt = pd.to_datetime(date)
        end_dt = start_dt + timedelta(days=5) # janela para garantir que pega um dia útil
        hist = t.history(start=start_dt.strftime('%Y-%m-%d'), end=end_dt.strftime('%Y-%m-%d'))
        if not hist.empty:
            return round(hist['Close'].iloc[0], 2)
        return 0.0
    except:
        return 0.0

def get_asset_basic_info(ticker: str) -> dict:
    """Busca o nome e tenta inferir o tipo do ativo."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        tipo = "Ações"
        quote_type = info.get("quoteType", "")
        if quote_type == "ETF":
            tipo = "ETFs"
        elif quote_type == "CRYPTOCURRENCY":
            tipo = "Cripto"
        return {"nome": info.get("shortName", info.get("longName", ticker)), "tipo": tipo}
    except:
        return {"nome": "", "tipo": "Ações"}

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
            t = yf.Ticker(ticker)
            info = t.info
            
            # 1. Data de IPO
            ipo_epoch = info.get("firstTradeDateEpoch")
            if ipo_epoch:
                ipo_date = datetime.fromtimestamp(ipo_epoch).strftime('%Y-%m-%d')
            else:
                try:
                    hist_max = t.history(period="max")
                    ipo_date = hist_max.index.min().strftime('%Y-%m-%d') if not hist_max.empty else "N/A"
                except:
                    ipo_date = "N/A"
            
            # 2. Análise do Balanço/DRE
            financials = t.financials
            lucro_consecutivo = "N/A"
            receita_sobe = "N/A"
            
            if financials is not None and not financials.empty:
                if "Net Income" in financials.index:
                    net_incomes = financials.loc["Net Income"].dropna().head(4)
                    if len(net_incomes) >= 1:
                        lucro_consecutivo = "Sim" if all(val > 0 for val in net_incomes) else "Não"
                
                if "Total Revenue" in financials.index:
                    revenues = financials.loc["Total Revenue"].dropna().head(4)
                    if len(revenues) >= 2:
                        receita_sobe = "Sim" if all(revenues.iloc[i] > revenues.iloc[i+1] for i in range(len(revenues)-1)) else "Não"
            
            # 3. ROIC
            roic_val = info.get("returnOnCapital") or info.get("returnOnAssets")
            roic = roic_val * 100 if isinstance(roic_val, (int, float)) else None

            # 4. Dividend Yield (%)
            dy_val = info.get("dividendYield")
            dy = dy_val if isinstance(dy_val, (int, float)) else None

            # 5. Market Cap (Bruto)
            m_cap = info.get("marketCap")
            
            # 6. ROE (%)
            roe_val = info.get("returnOnEquity")
            roe = roe_val * 100 if isinstance(roe_val, (int, float)) else None

            # 7. Preço e Valuation
            preco = info.get("currentPrice", info.get("regularMarketPrice"))
            pl = info.get("trailingPE")
            pvp = info.get("priceToBook")
                
            metrics.append({
                "Ticker": ticker,
                "Nome": info.get("shortName", "N/A"),
                "Setor": info.get("sector", "N/A"),
                "País": info.get("country", "N/A"),
                "Preço Atual": preco,
                "P/L (P/E)": pl,
                "P/VP (P/B)": pvp,
                "Div. Yield (%)": dy,
                "Market Cap": m_cap,
                "ROE (%)": roe,
                "ROIC (%)": roic,
                "Data IPO": ipo_date,
                "Lucro >0 (4A)?": lucro_consecutivo,
                "Receita Sobe?": receita_sobe
            })
        except Exception as e:
            metrics.append({
                "Ticker": ticker, "Nome": "Erro ao buscar dados", 
                "Setor": "-", "Preço Atual": None, "P/L (P/E)": None, 
                "P/VP (P/B)": None, "Div. Yield (%)": None, "Market Cap": None, "ROE (%)": None,
                "ROIC (%)": None, "Data IPO": "N/A", "Lucro >0 (4A)?": "N/A", "Receita Sobe?": "N/A"
            })
    return metrics

def calculate_portfolio_performance(ativos_transacoes):
    """
    Recebe uma lista de ativos e suas transações e calcula performance.
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
            
        compras = [t for t in item['transacoes'] if t.tipo_transacao == "Compra"]
        if not compras:
            continue
            
        custo_medio = sum(t.preco * t.quantidade for t in compras) / sum(t.quantidade for t in compras)
        
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
