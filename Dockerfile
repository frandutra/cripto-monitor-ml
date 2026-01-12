# 1. Cambiamos de 3.9 a 3.10 (o 3.11) para soportar la nueva sintaxis de tipos
FROM python:3.10-slim

# 2. Directorio de trabajo
WORKDIR /app

# 3. Instalamos dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiamos e instalamos librerías
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el resto de la app
COPY . .

# 6. Puerto
EXPOSE 8501

# 7. Ejecución
ENTRYPOINT ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]