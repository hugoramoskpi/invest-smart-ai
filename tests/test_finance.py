from app.finance import calculate_portfolio_performance
from types import SimpleNamespace

def test_calculate_portfolio_performance_empty():
    perf, total_inv, total_at = calculate_portfolio_performance([])
    assert perf == []
    assert total_inv == 0
    assert total_at == 0

def test_calculate_portfolio_performance_basic():
    # Simula dados do banco
    t1 = SimpleNamespace(quantidade=10, preco=100, tipo_transacao="Compra")
    dados = [{"ticker": "AAPL", "transacoes": [t1]}]
    
    # Nota: yfinance retornará 0 no teste se não houver internet ou se o ticker falhar,
    # mas a lógica de custo total deve funcionar.
    perf, total_inv, total_at = calculate_portfolio_performance(dados)
    
    assert total_inv == 1000
    assert len(perf) == 1
    assert perf[0]["Ativo"] == "AAPL"
    assert perf[0]["Custo Médio"] == 100
