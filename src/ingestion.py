import yfinance as yf
import pandas as pd
import os

def fetch_crypto_data(ticker="BTC-USD", period="60d", interval="5m"):
    """
    Extrae datos históricos de la API de Yahoo Finance.
    period: 1d, 5d, 7d, 1mo...
    interval: 1m, 2m, 5m, 15m, 60m, 1d...
    """
    print(f"Descargando datos para {ticker}...")
    data = yf.download(tickers=ticker, period=period, interval=interval)
    
    if data.empty:
        print("No se obtuvieron datos. Revisa el ticker o la conexión.")
        return None
    
    return data

def run_ingestion():
    # Prueba rápida
    df = fetch_crypto_data()
    if df is not None:
        print(df.head())
        # Crear carpeta data si no existe (en root del proyecto)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        data_dir = os.path.join(project_root, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Guardar para inspeccionar
        save_path = os.path.join(data_dir, 'raw_btc_data.csv')
        df.to_csv(save_path)
        print(f"Archivo guardado en {save_path}")
        return True
    return False

if __name__ == "__main__":
    run_ingestion()