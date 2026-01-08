import streamlit as st
import pandas as pd
import joblib
import yfinance as yf
import plotly.graph_objects as go
import os

# Configuración de la página
st.set_page_config(page_title="Financial Asset Predictor", layout="wide")

st.title("Financial Asset Real-Time Predictor 🚀")

# --- SECCIÓN 1: CARGA DEL MODELO ---
@st.cache_resource
def load_model():
    # Esto funcionará tanto en Windows como en Linux (Docker)
    model_path = os.path.join('models', 'crypto_model.pkl')
    
    if not os.path.exists(model_path):
        st.error(f"No se encontró el modelo en: {model_path}")
        return None
    
    return joblib.load(model_path)
data_pack = load_model()

if data_pack:
    model = data_pack['model']
    features = data_pack['features']

    # --- SECCIÓN 2: BARRA LATERAL ---
    st.sidebar.header("Configuración")
    symbol = st.sidebar.selectbox("Ticker", ["BTC-USD", "ETH-USD", "SYP", "AAPL"])
    update_button = st.sidebar.button("Actualizar Datos")

    # --- SECCIÓN 3: OBTENCIÓN Y LIMPIEZA DE DATOS (Data Engineering) ---
    # Bajamos datos del último día con intervalos de 1 minuto
    df = yf.download(symbol, period="1d", interval="1m")

    if not df.empty:
        # CORRECCIÓN DEL ERROR: Limpiamos el MultiIndex si existe
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Creamos los indicadores técnicos (Features) necesarios para el modelo
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['Close_Lag1'] = df['Close'].shift(1)
        df['Close_Lag2'] = df['Close'].shift(2)
        
        # Tomamos la última fila para la predicción
        last_row = df[features].tail(1)
        
        # Verificamos que tengamos suficientes datos para calcular las MA y Lags
        if not last_row.isnull().values.any():
            
            # --- SECCIÓN 4: INFERENCIA (Machine Learning) ---
            prediction = model.predict(last_row)[0]
            prob = model.predict_proba(last_row)[0]
            
            # Extraemos el precio actual como escalar para evitar el TypeError
            precio_actual = float(df['Close'].iloc[-1])

            # Mostrar métricas principales
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Precio Actual", f"${precio_actual:,.2f}")
            with col2:
                resultado = "SUBE 📈" if prediction == 1 else "BAJA 📉"
                confianza = max(prob) * 100
                st.metric("Predicción Próxima Vela", resultado, f"Confianza: {confianza:.1f}%")

            # --- SECCIÓN 5: VISUALIZACIÓN (Storytelling) ---
            st.subheader(f"Gráfico de Tiempo Real: {symbol}")
            
            fig = go.Figure(data=[
                # Velas Japonesas
                go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="Precio"
                ),
                # Línea de Media Móvil
                go.Scatter(
                    x=df.index, 
                    y=df['MA_20'], 
                    line=dict(color='yellow', width=1.5), 
                    name="Media Móvil 20"
                )
            ])

            fig.update_layout(
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar tabla de datos crudos (opcional, útil para debug)
            with st.expander("Ver datos procesados"):
                st.write(df.tail(10))
        else:
            st.warning("Esperando a recolectar suficientes datos para calcular indicadores técnicos (MA_20)...")
    else:
        st.error("No se pudieron obtener datos de la API. Verifica el Ticker.")