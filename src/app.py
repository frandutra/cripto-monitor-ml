import streamlit as st
import pandas as pd
import joblib
import yfinance as yf
import plotly.graph_objects as go
import os
import requests
from database import init_db, save_prediction, get_history, update_last_result
from streamlit_autorefresh import st_autorefresh

from dotenv import load_dotenv

# Load environment variables from .env file (parent directory of src)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
load_dotenv(os.path.join(project_root, '.env'))

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
st.set_page_config(page_title="Crypto Monitor", layout="wide", page_icon="🤖")
st.title("Crypto Monitor")

# Inicializar DB (Crea tablas si no existen)
try:
    init_db()
except Exception as e:
    st.error(f"Error de conexión con la Base de Datos: {e}")

# Refresco automático cada 60 segundos
count = st_autorefresh(interval=60000, key="bot_refresh")

@st.cache_resource
def load_model(ticker="BTC-USD"):
    safe_ticker = ticker.replace("-", "_")
    model_filename = f'crypto_model_{safe_ticker}.pkl'
    model_path = os.path.join(project_root, 'models', model_filename)
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

from ingestion import run_ingestion
from train_model import train_model
from features import calculate_features

# ... (imports existing)

# ... (load_model func existing)

# SIDEBAR se define ANTES de cargar el modelo en esta arquitectura propuesta
st.sidebar.header("⚙️ Configuración")
# ... (previous code)
symbol = st.sidebar.selectbox("Activo", ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "ADA-USD", "XRP-USD"])

data_pack = load_model(symbol)
training_interval = st.sidebar.selectbox("Intervalo de Entrenamiento", ["1m", "5m", "15m", "1h", "1d"], index=1)
training_period = st.sidebar.selectbox(
    "Periodo de Historia", 
    ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], 
    index=2,
    help="Nota: Yahoo Finance limita la historia para intervalos cortos.\n- '1m' permite máx ~7 días.\n- '5m' permite máx ~60 días.\nPara periodos largos (meses/años) usa intervalos de 1h o 1d."
)
auto_save = st.sidebar.checkbox("Guardado Automático", value=True)
conf_threshold = st.sidebar.slider("Umbral Telegram (%)", 50, 95, 80)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Actualizar Modelo"):
    with st.spinner("Descargando nuevos datos y re-entrenando..."):
        try:
            # 1. Ingesta
            if run_ingestion(ticker=symbol, period=training_period, interval=training_interval):
                st.sidebar.success(f"Datos actualizados ({training_period}).")
                
                # 2. Entrenamiento
                train_model(ticker=symbol, interval=training_interval)
                st.sidebar.success(f"Modelo para {symbol} re-entrenado.")
                
                # 3. Recarga
                load_model.clear() # Limpiar cache de st
                st.cache_resource.clear()
                
                st.sidebar.success("¡Modelo recargado! 🎉")
                st.rerun()
            else:
                st.sidebar.error("Falló la descarga de datos.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

if data_pack:
    model = data_pack['model']
    features = data_pack['features']
    model_interval = data_pack.get('interval', '1m')

    # --- OBTENCIÓN DE DATOS Y ESTADO ---
    # Determinar periodo seguro según intervalo
    fetch_period = "5d" if model_interval == "1m" else "60d"
    if model_interval == "1d": fetch_period = "2y" # Necesitamos suficiente historia para MA

    df = yf.download(symbol, period=fetch_period, interval=model_interval, progress=False)
    history_df = get_history()

    if not df.empty:
        # Limpieza de columnas (yfinance a veces trae MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Cálculo de Indicadores (Centralizado)
        df = calculate_features(df)
        
        # Seleccionar features correctos
        last_row = df[features].tail(1)
        # Reemplazar infinitos o NaNs si ocurren por volatilidad explsiva
        last_row.replace([float('inf'), float('-inf')], 0, inplace=True)
        last_row.fillna(0, inplace=True)
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
            pred_text = "SUBE 📈" if prediction == 1 else "BAJA 📉"
            c2.metric("Predicción", pred_text, f"{confianza:.1f}%")
            # Cálculo de Win Rate para el header
            if not history_df.empty:
                valid = history_df.dropna(subset=['result'])
                if len(valid) > 0:
                    wr = (valid['result'].sum() / len(valid)) * 100
                    c3.metric("Win Rate", f"{wr:.1f}%", f"{len(valid)} trades")
            c4.metric("Refresco", f"#{count}")
            
            # Selector de Zoom
            zoom_period = st.select_slider(
                "🔎 Zoom del Gráfico (Velas)", 
                options=[50, 100, 200, 500, 1000, 2000, "Todo"],
                value=200
            )
            
            # Filtrado de datos para visualización
            if zoom_period != "Todo":
                df_display = df.tail(zoom_period)
            else:
                df_display = df
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df_display.index, open=df_display['Open'], high=df_display['High'], 
                low=df_display['Low'], close=df_display['Close'], name="Precio"
            ))
            fig.add_trace(go.Scatter(x=df_display.index, y=df_display['MA_20'], line=dict(color='yellow', width=2), name="MA20"))
            fig.update_layout(
                template="plotly_dark", 
                height=450, 
                margin=dict(t=30, b=10), 
                xaxis_rangeslider_visible=False,
                title=f"Gráfico {symbol} - {len(df_display)} velas"
            )
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
                    "confidence": st.column_config.ProgressColumn("Confianza", min_value=0, max_value=100, format="%.1f%%"),
                    "timestamp": "Fecha/Hora"
                },
                use_container_width=True,
                hide_index=True
            )

    # --- 5. DATA SCIENCE: INTERPRETABILIDAD DEL MODELO ---
    with st.expander("🧠 Explicabilidad del Modelo (Feature Importance)", expanded=False):
        st.caption("Este análisis muestra qué indicadores técnicos tienen más peso en la decisión del algoritmo.")
        
        imp_df = data_pack.get('feature_importance')
        
        if imp_df is not None and not imp_df.empty:
            # Ordenar para visualización estética (Mayor a menor ya viene, pero aseguramos para gráfico)
            imp_df = imp_df.sort_values(by='Importance', ascending=True)
            
            # Gráfico de barras horizontal
            fig_xai = go.Figure(go.Bar(
                x=imp_df['Importance'],
                y=imp_df['Feature'],
                orientation='h',
                marker=dict(
                    color=imp_df['Importance'],
                    colorscale='Viridis'
                )
            ))
            
            fig_xai.update_layout(
                title="Peso de Variables en la Predicción",
                xaxis_title="Importancia Relativa (0-1)",
                yaxis_title="Indicador / Feature",
                template="plotly_dark",
                height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_xai, use_container_width=True)
            
            # Insights generados dinámicamente
            top_feature = imp_df.iloc[-1]['Feature']
            st.info(f"💡 **Insight:** El modelo actual depende fuertemente de **{top_feature}**. Esto sugiere que para {symbol}, el comportamiento de {top_feature} es el predictor más fiable.")
        else:
            st.warning("⚠️ Este modelo es antiguo y no contiene datos de explicabilidad. Por favor, re-entrena el modelo usando el botón 'Actualizar Modelo' en la barra lateral.")


else:
    st.warning(f"⚠️ No se encontró el modelo para {symbol}. Por favor, presiona 'Actualizar Modelo' en el menú lateral para entrenar uno nuevo.")