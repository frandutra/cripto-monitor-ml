# Documentación Funcional - Crypto Monitor ML

## 1. Descripción General
**Crypto Monitor ML** es un sistema inteligente de monitoreo y predicción de precios de criptomonedas en tiempo real. Su objetivo principal es asistir a traders e inversores proporcionando señales de compra/venta (sube/baja) basadas en un modelo de Machine Learning (Random Forest) entrenado con datos históricos.

El sistema opera de forma autónoma, descargando datos de mercado minuto a minuto, procesándolos, y generando predicciones acompañadas de un nivel de confianza.

## 2. Características Principales

### 🔮 Predicción en Tiempo Real
- **Frecuencia**: Genera una nueva predicción cada 60 segundos.
- **Activos Soportados**: BTC-USD (Bitcoin), extensible a otros pares como ETH-USD, etc.
- **Señal**: Indica si el precio cerrará "AL ALZA" o "A LA BAJA" en el próximo minuto.
- **Confianza**: Asigna un porcentaje de certeza a cada predicción (%).

### 🤖 Bot Autónomo y Alertas
- El sistema funciona 24/7 sin intervención humana.
- **Integración con Telegram**: Envía alertas instantáneas al usuario cuando detecta una oportunidad con alta probabilidad de éxito (Confianza > 80% configurable).

### 📊 Dashboard Interactivo (Streamlit)
Una interfaz web amigable que permite:
- Ver el precio actual y el gráfico de velas en vivo.
- Observar la predicción actual y el tiempo para la próxima actualización.
- Consultar el historial de predicciones pasadas.
- Visualizar métricas de rendimiento (Win Rate) y distribución de señales.

### 💾 Persistencia y Auditoría
- Todas las predicciones se guardan automáticamente en una base de datos **PostgreSQL**.
- El sistema "auto-evalúa" sus predicciones pasadas comparándolas con lo que realmente ocurrió en el mercado, actualizando el historial con "ACIERTO" o "FALLO".

## 3. Flujo del Usuario

1. **Acceso**: El usuario ingresa a la aplicación web (localmente en el puerto 8501).
2. **Monitoreo**:
   - En el panel principal, observa el comportamiento actual de Bitcoin.
   - Revisa la caja de "Predicción" para ver la señal actual.
3. **Configuración (Barra Lateral)**:
   - Puede cambiar el activo (ej. a ETH-USD).
   - Ajustar el umbral de confianza para recibir más o menos alertas en Telegram.
4. **Recepción de Alertas**:
   - Si el usuario no está frente a la pantalla, recibirá una notificación en su Telegram personal únicamente cuando el mercado presente una oportunidad clara según el modelo.

## 4. Lógica de Negocio (Modelo Predictivo)
El "cerebro" del sistema no predice precios exactos (ej. "$95,500"), sino **tendencias**:
- Analiza el *momentum* (retornos a 1 y 2 minutos) y la desviación del precio respecto a su media móvil.
- Si el modelo detecta patrones alcistas fuertes, emite una probabilidad alta de "SUBE".
- Esta abstracción permite que el modelo funcione correctamente independientemente de si Bitcoin vale $20k o $100k (es agnóstico al precio absoluto).
