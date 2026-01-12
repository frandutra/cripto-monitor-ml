# 🤖 Crypto Predictor Bot v1.1

Un bot autónomo de predicción de criptomonedas desarrollado con **Python**, **Streamlit** y **Machine Learning**. El sistema descarga datos en tiempo real, genera predicciones de tendencia y envía alertas inteligentes a **Telegram**.

## 🚀 Características clave
* **Predicción en tiempo real:** Análisis minuto a minuto usando `yfinance`.
* **Visualización Interactiva:** Gráficos de velas (Candlestick) con indicadores de tendencia (MA 20).
* **Alertas de Telegram:** Notificaciones automáticas cuando la confianza del modelo supera un umbral configurable.
* **Historial y Win Rate:** Base de datos SQLite integrada para trackear el rendimiento del bot.
* **Infraestructura Profesional:** Totalmente dockerizado y configurable mediante variables de entorno.

---

## 🛠️ Tecnologías utilizadas
* **Lenguaje:** Python 3.9+
* **ML Stack:** Scikit-learn, Pandas, Joblib.
* **Dashboard:** Streamlit + Plotly.
* **DevOps:** Docker, Docker Compose.
* **Base de Datos:** SQLite.

---

## 📦 Instalación y Despliegue

Sigue estos pasos para correr el proyecto localmente usando Docker:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/tu-usuario/nombre-de-tu-repo.git](https://github.com/tu-usuario/nombre-de-tu-repo.git)
cd nombre-de-tu-repo
```

### 2. Configurar Variables de Entorno
Crea un archivo .env en la raíz del proyecto (puedes basarte en .env.example):

```bash
TELEGRAM_TOKEN=tu_token_de_botfather
TELEGRAM_CHAT_ID=tu_id_de_usuario
```
### 3. Levantar con Docker Compose

```bash
docker-compose up --build -d
```
4. Acceder a la aplicación
Abre tu navegador y entra en: http://localhost:8501
