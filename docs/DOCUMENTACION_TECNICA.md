# Documentación Técnica - Arquitectura y Código

## 1. Arquitectura del Sistema
El proyecto sigue una arquitectura de microservicios contenerizada utilizando **Docker**.

### Componentes:
1.  **App Container (`predictor-bot`)**:
    *   Ejecuta la lógica de negocio en Python.
    *   Corre la interfaz de usuario con Streamlit.
    *   Gestiona la conexión con la API de Yahoo Finance y Telegram.
2.  **Database Container (`crypto_db`)**:
    *   Instancia de **PostgreSQL** para persistencia de datos.
    *   Almacena el historial de predicciones y resultados.

## 2. Estructura de Archivos y Responsabilidades

### 📂 Raíz del Proyecto (`cripto-monitor-ml/`)

*   **`docker-compose.yml`**:
    *   **Función**: Orquestador de servicios. Define los dos contenedores (`db` y `predictor-bot`), sus redes, volúmenes (para persistencia de DB y modelos) y variables de entorno.
*   **`Dockerfile`**:
    *   **Función**: Receta de construcción para la imagen de la aplicación. Instala Python 3.11, dependencias del sistema y librerías de Python.
*   **`.env`**:
    *   **Función**: Configuración sensible (Credenciales de DB, Tokens de Telegram). **No debe subirse al repositorio**.
*   **`requirements.txt`**:
    *   **Función**: Lista de dependencias de Python (`streamlit`, `pandas`, `scikit-learn`, `psycopg2`, etc.).

### 📂 Código Fuente (`src/`)

#### `src/app.py` (Controlador Principal)
*   **Rol**: Punto de entrada de la aplicación Web.
*   **Responsabilidades**:
    *   Inicializar conexión a DB.
    *   Cargar el modelo ML (`models/crypto_model.pkl`).
    *   **Ingesta en Tiempo Real**: Llama a `yfinance` cada 60s.
    *   **Ingeniería de Características**: Transforma datos crudos en features relativos (`Returns_1m`, `Dist_MA_20`) idénticos a los del entrenamiento.
    *   **Inferencia**: Ejecuta `model.predict()`.
    *   **Lógica de Negocio**: Evalúa si enviar alerta a Telegram.
    *   **UI**: Renderiza gráficos y tablas con Streamlit.

#### `src/database.py` (Capa de Datos)
*   **Rol**: Abstracción de acceso a datos (DAO).
*   **Responsabilidades**:
    *   Manejar conexión con PostgreSQL (con reintentos).
    *   `init_db()`: Crea tabla `predictions` si no existe.
    *   `save_prediction()`: Inserta nuevos registros.
    *   `get_history()`: Recupera datos para el dashboard.
    *   `update_last_result()`: Actualiza si una predicción fue correcta o fallida a posteriori.

#### `src/train_model.py` (Pipeline de Entrenamiento)
*   **Rol**: Script offline para generar el "cerebro" del bot.
*   **Responsabilidades**:
    *   Carga datos históricos desde `data/raw_btc_data.csv`.
    *   Limpia y preprocesa los datos.
    *   **Feature Engineering**: Crea las variables relativas.
    *   Entrena el modelo `RandomForestClassifier`.
    *   Serializa y guarda el modelo en `models/crypto_model.pkl`.

#### `src/ingestion.py` (Ingesta Histórica)
*   **Rol**: Utilidad para descargar datasets grandes.
*   **Uso**: Se ejecuta manualmente cuando se quiere actualizar el dataset base de entrenamiento (`data/csv`).

#### `src/inspect_model.py` (Diagnóstico)
*   **Rol**: Script de "Sanity Check".
*   **Uso**: Verifica que el archivo `.pkl` se pueda cargar y que responda con varianza ante inputs aleatorios, útil para depurar si el modelo está "congelado".

## 3. Flujo de Datos

1.  **Entrenamiento (Offline)**:
    `Yahoo Finance API` -> `ingestion.py` -> `CSV` -> `train_model.py` -> **`crypto_model.pkl`**

2.  **Inferencia (Online)**:
    `Yahoo Finance API` -> `app.py` -> *(Calculo Features)* -> **`crypto_model.pkl`** -> `Predicción` -> `PostgreSQL`

3.  **Consumo**:
    `PostgreSQL` -> `app.py` -> `Dashboard Streamlit` / `Alerta Telegram`

## 4. Relaciones Clave
*   **Consistencia**: Es crítico que la **Ingeniería de Características** en `train_model.py` (líneas 30-45) sea idéntica a la de `app.py` (líneas 75-85). Si cambian en uno, deben cambiar en el otro.
*   **Docker Networking**: `app.py` se conecta a la base de datos usando el host `db` (nombre del servicio en docker-compose), no `localhost`.
