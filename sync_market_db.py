import sys
import os
import pandas as pd
import concurrent.futures
from datetime import datetime

# Adiciona o diretório 'app' ao path para importar as funções
sys.path.append(os.path.join(os.getcwd(), 'app'))

from finance import get_asset_metrics
from screener_tickers import get_all_market_tickers

DB_PATH = "market_database.csv"

def sync_market_data():
    print(f"[{datetime.now()}] Iniciando sincronização massiva do mercado...")
    
    # Busca todos os tickers (BR + EUA ~4000)
    tickers = get_all_market_tickers()
    total = len(tickers)
    print(f"Total de ativos identificados: {total}")
    
    # Processa em lotes para evitar bloqueios e gerenciar memória
    batch_size = 50
    all_data = []
    
    # Usando ThreadPoolExecutor para paralelizar as requisições ao Yahoo Finance
    # Usaremos no máximo 10 workers para não ser bloqueado por excesso de requisições
    max_workers = 10
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Divide em lotes de 50 para processar via get_asset_metrics
        future_to_batch = {
            executor.submit(get_asset_metrics, tickers[i:i + batch_size]): i 
            for i in range(0, total, batch_size)
        }
        
        processed = 0
        for future in concurrent.futures.as_completed(future_to_batch):
            try:
                data = future.result()
                all_data.extend(data)
                processed += len(data)
                print(f"Progresso: {processed}/{total} ativos processados...")
            except Exception as e:
                print(f"Erro ao processar lote: {e}")

    # Salva em CSV
    df = pd.DataFrame(all_data)
    df.to_csv(DB_PATH, index=False, encoding='utf-8-sig')
    print(f"[{datetime.now()}] Sincronização concluída! Arquivo salvo em: {DB_PATH}")

if __name__ == "__main__":
    sync_market_data()
