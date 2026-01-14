import psycopg2
from psycopg2 import extras
import os
import time

def get_connection():
    # Reintento de conexión por si Postgres tarda en arrancar
    max_retries = 5
    for i in range(max_retries):
        try:
            return psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(2)
                continue
            raise e

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Sintaxis de Postgres (cambia un poco respecto a SQLite)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            symbol TEXT,
            entry_price FLOAT,
            prediction INTEGER,
            confidence FLOAT,
            result INTEGER
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_prediction(symbol, price, prediction, confidence):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO predictions (symbol, entry_price, prediction, confidence) VALUES (%s, %s, %s, %s)",
        (symbol, price, prediction, confidence)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_history(limit=10):
    conn = get_connection()
    # Usamos DictCursor para que Streamlit reciba los datos como si fuera un diccionario
    cur = conn.cursor(cursor_factory=extras.DictCursor)
    cur.execute("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    import pandas as pd
    return pd.DataFrame(rows, columns=['id', 'timestamp', 'symbol', 'entry_price', 'prediction', 'confidence', 'result'])

def update_last_result(pred_id, result):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE predictions SET result = %s WHERE id = %s", (result, pred_id))
    conn.commit()
    cur.close()
    conn.close()