import yfinance as yf
import pandas as pd
import os

def fetch_crypto_data(ticker="BTC-USD", period="7d", interval="1m"):
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

if __name__ == "__main__":
    # Prueba rápida
    df = fetch_crypto_data()
    if df is not None:
        print(df.head())
        # Crear carpeta data si no existe
        os.makedirs('data', exist_ok=True)
        # Guardar para inspeccionar
        df.to_csv('data/raw_btc_data.csv')
        print("Archivo guardado en data/raw_btc_data.csv")