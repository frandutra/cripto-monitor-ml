import streamlit as st
import pandas as pd
import joblib
import yfinance as yf
import plotly.graph_objects as go
import os
from database import init_db, save_prediction, get_history
from streamlit_autorefresh import st_autorefresh

# Configuración
st.set_page_config(page_title="Crypto Bot v1.0", layout="wide")
st.title("Crypto Predictor Bot Autónomo 🤖")

init_db()
history_df = pd.DataFrame()

# Refresco cada 60 segundos
count = st_autorefresh(interval=60000, key="bot_refresh")

@st.cache_resource
def load_model():
    model_path = os.path.join('models', 'crypto_model.pkl')
    return joblib.load(model_path) if os.path.exists(model_path) else None

data_pack = load_model()

if data_pack:
    model = data_pack['model']
    features = data_pack['features']

    st.sidebar.header("🤖 Configuración del Bot")
    symbol = st.sidebar.selectbox("Activo a Monitorear", ["BTC-USD", "ETH-USD"])
    auto_save = st.sidebar.checkbox("Guardado Automático Activo", value=True)

    # 1. Obtención de datos
    df = yf.download(symbol, period="1d", interval="1m")
    history_df = get_history()

    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Cálculo de indicadores para el gráfico
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['Close_Lag1'] = df['Close'].shift(1)
        df['Close_Lag2'] = df['Close'].shift(2)
        
        last_row = df[features].tail(1)
        precio_actual = float(df['Close'].iloc[-1])

        if not last_row.isnull().values.any():
            prediction = int(model.predict(last_row)[0])
            prob = model.predict_proba(last_row)[0]
            confianza = float(max(prob) * 100)

            # --- LÓGICA DE AUTO-CALIFICACIÓN ---
            if not history_df.empty:
                last_pred = history_df.iloc[0]
                if pd.isna(last_pred['result']):
                    p_entrada = last_pred['entry_price']
                    pred_hecha = last_pred['prediction']
                    id_pred = int(last_pred['id'])
                    
                    exito = 1 if (pred_hecha == 1 and precio_actual > p_entrada) or \
                                 (pred_hecha == 0 and precio_actual < p_entrada) else 0
                    
                    from database import update_last_result
                    update_last_result(id_pred, exito)
                    st.toast(f"Resultado actualizado ID {id_pred}: {'✅' if exito else '❌'}")
                    history_df = get_history()

            # --- GUARDADO AUTOMÁTICO ---
            if auto_save:
                already_saved = False
                if not history_df.empty:
                    last_entry_time = pd.to_datetime(history_df.iloc[0]['timestamp'])
                    if (pd.Timestamp.now() - last_entry_time).seconds < 55:
                        already_saved = True

                if not already_saved:
                    save_prediction(symbol, precio_actual, prediction, confianza)
                    st.toast(f"✅ Auto-guardado: {symbol}", icon="💾")
                    history_df = get_history()

            # Visualización Superior
            c1, c2, c3 = st.columns(3)
            c1.metric("Precio Actual", f"${precio_actual:,.2f}")
            c2.metric("Refrescos", count)
            c3.metric("Predicción", "SUBE 📈" if prediction == 1 else "BAJA 📉", f"{confianza:.1f}%")
            
            # Mensaje de éxito/fallo anterior
            if not history_df.empty:
                ult = history_df.iloc[0]
                if not pd.isna(ult['result']):
                    if ult['result'] == 1: st.success(f"🎯 Último acierto en {ult['symbol']}")
                    else: st.error(f"❌ Último fallo en {ult['symbol']}")

            # --- GRÁFICO CON LÍNEA AMARILLA (MA_20) ---
            fig = go.Figure()
            # Velas
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="Precio"
            ))
            # Línea de tendencia (MA_20)
            fig.add_trace(go.Scatter(
                x=df.index, y=df['MA_20'], 
                line=dict(color='yellow', width=2), 
                name="Media Móvil 20"
            ))
            
            fig.update_layout(template="plotly_dark", height=450, margin=dict(t=0, b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

    # --- SECCIÓN ANALÍTICA ---
    st.write("---")
    if not history_df.empty:
        # Win Rate Metric
        if 'result' in history_df.columns and history_df['result'].notnull().any():
            valid_results = history_df.dropna(subset=['result'])
            win_rate = (valid_results['result'].sum() / len(valid_results)) * 100
            st.metric("Win Rate del Bot", f"{win_rate:.1f}%")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Distribución**")
            st.bar_chart(history_df['prediction'].map({1: 'SUBE', 0: 'BAJA'}).value_counts())
        with col_b:
            st.markdown("**Confianza Histórica**")
            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
            st.line_chart(history_df.set_index('timestamp')['confidence'])
        
        st.subheader("📜 Historial de Operaciones")
        st.dataframe(history_df.sort_values(by='timestamp', ascending=False), use_container_width=True)