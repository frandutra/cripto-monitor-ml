import streamlit as st
import pandas as pd
import joblib
import yfinance as yf
import plotly.graph_objects as go
import os
import requests
from database import init_db, save_prediction, get_history, update_last_result
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURACIÓN DE AMBIENTE ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": message, 
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        st.sidebar.error(f"Error Telegram: {e}")

# --- CONFIGURACIÓN DE UI ---
st.set_page_config(page_title="Crypto Bot Pro v1.2", layout="wide", page_icon="🤖")
st.title("Crypto Predictor Bot Autónomo 🤖")

# Inicializar DB (Crea tablas si no existen)
try:
    init_db()
except Exception as e:
    st.error(f"Error de conexión con la Base de Datos: {e}")

# Refresco automático cada 60 segundos
count = st_autorefresh(interval=60000, key="bot_refresh")

@st.cache_resource
def load_model():
    model_path = os.path.join('models', 'crypto_model.pkl')
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

data_pack = load_model()

if data_pack:
    model = data_pack['model']
    features = data_pack['features']

    # --- SIDEBAR ---
    st.sidebar.header("⚙️ Configuración")
    symbol = st.sidebar.selectbox("Activo", ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD"])
    auto_save = st.sidebar.checkbox("Guardado Automático", value=True)
    conf_threshold = st.sidebar.slider("Umbral Telegram (%)", 50, 95, 80)

    # --- OBTENCIÓN DE DATOS Y ESTADO ---
    df = yf.download(symbol, period="1d", interval="1m", progress=False)
    history_df = get_history()

    if not df.empty:
        # Limpieza de columnas (yfinance a veces trae MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Cálculo de Indicadores
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['Close_Lag1'] = df['Close'].shift(1)
        df['Close_Lag2'] = df['Close'].shift(2)
        
        last_row = df[features].tail(1)
        precio_actual = float(df['Close'].iloc[-1])

        if not last_row.isnull().values.any():
            # Predicción del Modelo
            print(f"DEBUG - Datos para predicción:\n{last_row}")
            prediction = int(model.predict(last_row)[0])
            prob = model.predict_proba(last_row)[0]
            confianza = float(max(prob) * 100)

            # --- 1. LÓGICA DE AUTO-CALIFICACIÓN ---
            if not history_df.empty:
                last_pred = history_df.iloc[0]
                # Si la última predicción aún no tiene resultado (NULL)
                if pd.isna(last_pred['result']):
                    p_entrada = last_pred['entry_price']
                    pred_hecha = last_pred['prediction']
                    id_pred = int(last_pred['id'])
                    
                    exito = 1 if (pred_hecha == 1 and precio_actual > p_entrada) or \
                                 (pred_hecha == 0 and precio_actual < p_entrada) else 0
                    
                    update_last_result(id_pred, exito)
                    st.toast(f"Resultado actualizado ID {id_pred}", icon="⚖️")
                    history_df = get_history() # Recargar con el resultado nuevo

            # --- 2. LÓGICA DE GUARDADO Y TELEGRAM ---
            if auto_save:
                already_saved = False
                if not history_df.empty:
                    last_entry_time = pd.to_datetime(history_df.iloc[0]['timestamp'])
                    # Evitar duplicados en el mismo minuto
                    if (pd.Timestamp.now(tz='UTC').tz_localize(None) - last_entry_time.tz_localize(None)).seconds < 55:
                        already_saved = True

                if not already_saved:
                    save_prediction(symbol, precio_actual, prediction, confianza)
                    st.toast(f"✅ Nueva predicción guardada", icon="💾")
                    
                    if confianza >= conf_threshold:
                        emoji = "📈" if prediction == 1 else "📉"
                        txt = "SUBE" if prediction == 1 else "BAJA"
                        mensaje = (
                            f"🔔 *NUEVA PREDICCIÓN*\n\n"
                            f"Activo: `{symbol}`\n"
                            f"Precio: `${precio_actual:,.2f}`\n"
                            f"Predicción: *{txt}* {emoji}\n"
                            f"Confianza: `{confianza:.1f}%`"
                        )
                        send_telegram_alert(mensaje)
                    
                    history_df = get_history()

            # --- 3. DASHBOARD VISUAL ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Precio Actual", f"${precio_actual:,.2f}")
            c2.metric("Refresco", f"#{count}")
            
            pred_text = "SUBE 📈" if prediction == 1 else "BAJA 📉"
            c3.metric("Predicción", pred_text, f"{confianza:.1f}%")
            
            # Cálculo de Win Rate para el header
            if not history_df.empty:
                valid = history_df.dropna(subset=['result'])
                if len(valid) > 0:
                    wr = (valid['result'].sum() / len(valid)) * 100
                    c4.metric("Win Rate", f"{wr:.1f}%", f"{len(valid)} trades")

            # Gráfico de Velas
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], 
                low=df['Low'], close=df['Close'], name="Precio"
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df['MA_20'], line=dict(color='yellow', width=2), name="MA20"))
            fig.update_layout(template="plotly_dark", height=450, margin=dict(t=30, b=10), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, on_select="rerun")

    # --- 4. HISTORIAL Y ANALÍTICA ---
    st.write("---")
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("📊 Distribución")
        if not history_df.empty:
            dist = history_df['prediction'].map({1: 'SUBE', 0: 'BAJA'}).value_counts()
            st.bar_chart(dist)
    
    with col_right:
        st.subheader("📜 Registro en tiempo real (PostgreSQL)")
        if not history_df.empty:
            # Formatear tabla para lectura humana
            display_df = history_df.copy()
            display_df['result'] = display_df['result'].map({1: "✅ ACIERTO", 0: "❌ FALLO", None: "⏳ PENDIENTE"})
            display_df['prediction'] = display_df['prediction'].map({1: "SUBE", 0: "BAJA"})
            
            st.dataframe(
                display_df.sort_values(by='timestamp', ascending=False),
                column_config={
                    "entry_price": st.column_config.NumberColumn("Precio Entrada", format="$%.2f"),
                    "confidence": st.column_config.ProgressColumn("Confianza", min_value=0, max_value=100),
                    "timestamp": "Fecha/Hora"
                },
                use_container_width=True,
                hide_index=True
            )
else:
    st.warning("⚠️ No se encontró el modelo en `models/crypto_model.pkl`. Por favor, entrena el modelo primero.")