# 🤖 Crypto Predictor Bot v1.2

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Machine Learning](https://img.shields.io/badge/ML-Random%20Forest-orange.svg)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)

Un bot autónomo de monitoreo y predicción de criptomonedas desarrollado con un enfoque en **Ingeniería de Datos** y **Machine Learning**. El sistema no solo visualiza el mercado, sino que toma decisiones basadas en patrones técnicos históricos.

---

## 🌟 Características Principales

*   **🔮 Predicción Basada en Clasificación:** Utiliza un modelo de **Random Forest** para predecir si el precio subirá o bajará en el próximo intervalo (ej. 5 min).
*   **📊 Dashboard en Tiempo Real:** Interfaz profesional con Streamlit y Plotly para seguimiento de trades y métricas de rendimiento.
*   **📈 Estadísticas de Validación:** Sección dedicada a métricas de clasificación (Accuracy, Precision, Recall, F1, ROC-AUC) y Matriz de Confusión.
*   **🔔 Alertas Inteligentes:** Integración con Telegram Bot API para notificaciones de alta confianza (>80%).
*   **🧠 Feature Engineering Avanzado:** Cálculo automático de RSI, Bandas de Bollinger, Medias Móviles y retornos logarítmicos.
*   **🗄️ Persistencia con PostgreSQL:** Almacenamiento robusto de cada predicción y su resultado posterior para cálculo automático de **Win Rate**.
*   **🐳 Dockerizado:** Despliegue sencillo con Docker Compose (Contenedor de App + Base de Datos).

---

## 🧠 ¿Por qué Random Forest y no Regresión Lineal?

Para este proyecto elegí **Random Forest Classifier** sobre modelos lineales tradicionales por:
1.  **No-linealidad:** Los mercados financieros son caóticos. Los árboles de decisión capturan relaciones complejas que una línea recta ignora.
2.  **Explicabilidad:** El modelo nos permite ver la importancia de cada variable (Feature Importance), ayudándonos a entender qué indicador técnico está "mandando" en el mercado actual.
3.  **Robustez:** Es menos sensible a valores atípicos (outliers), comunes en la volatilidad de las criptomonedas.

---

## 🛠️ Stack Tecnológico

*   **Backend:** Python 3.11
*   **ML Stack:** Scikit-learn, Pandas, Joblib
*   **Database:** PostgreSQL
*   **API:** Yahoo Finance (via `yfinance`)
*   **Visualización:** Streamlit, Plotly
*   **Infraestructura:** Docker & Docker Compose

---

## 🚀 Instalación Rápida

### 1. Requisitos Previos
*   Docker y Docker Compose instalados.
*   Un Bot de Telegram (puedes crearlo en 1 min con [@BotFather](https://t.me/botfather)).

### 2. Configuración
Crea un archivo `.env` en la raíz (usa `.env.example` como base):
```env
TELEGRAM_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_id
DB_NAME=crypto_monitor
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=db
DB_PORT=5432
```

### 3. Despliegue
```bash
docker-compose up --build -d
```
Accede a la UI en: `http://localhost:8501`

---

## 📈 Próximos Pasos (Roadmap)
- [ ] Implementar modelos de Deep Learning (LSTM) para series de tiempo.
- [ ] Agregar soporte para múltiples exchanges via CCXT.
- [ ] Sistema de Backtesting avanzado con simulación de comisiones.

---

## 📄 Licencia
Este proyecto está bajo la Licencia MIT. Siéntete libre de usarlo, mejorarlo y compartirlo.

---
*Desarrollado con ❤️ para la comunidad de Data Science y Trading.*
