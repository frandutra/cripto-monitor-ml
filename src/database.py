import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join('models', 'crypto_history.db')

def get_connection():
    """Crea una conexión y un cursor listos para usar."""
    conn = sqlite3.connect(DB_PATH)
    return conn, conn.cursor()

def init_db():
    """Inicializa la base de datos y las tablas si no existen."""
    if not os.path.exists('models'):
        os.makedirs('models')
    
    conn, cursor = get_connection()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            symbol TEXT,
            entry_price REAL,
            prediction INTEGER,
            confidence REAL,
            result INTEGER  -- 1 para acierto, 0 para fallo, NULL para pendiente
        )
    ''')
    conn.commit()
    conn.close()

def save_prediction(symbol, price, pred, conf):
    """Guarda una nueva predicción."""
    conn, cursor = get_connection()
    cursor.execute('''
        INSERT INTO predictions (symbol, entry_price, prediction, confidence)
        VALUES (?, ?, ?, ?)
    ''', (symbol, price, int(pred), float(conf)))
    conn.commit()
    conn.close()

def update_last_result(prediction_id, result):
    """Actualiza el resultado de una predicción específica."""
    conn, cursor = get_connection()
    cursor.execute('''
        UPDATE predictions SET result = ? WHERE id = ?
    ''', (result, prediction_id))
    conn.commit()
    conn.close()

def get_history():
    """Recupera todo el historial para mostrarlo en Streamlit."""
    conn, _ = get_connection()
    query = "SELECT * FROM predictions ORDER BY timestamp DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df