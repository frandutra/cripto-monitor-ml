# 1. Imagen base de Python ligera
FROM python:3.9-slim

# 2. Directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Instalamos dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiamos e instalamos las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el resto del proyecto
COPY . .

# 6. Exponemos el puerto de Streamlit
EXPOSE 8501

# 7. Comando para arrancar la app
ENTRYPOINT ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]