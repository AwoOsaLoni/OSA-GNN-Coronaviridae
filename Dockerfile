# Usamos una imagen ligera de Python con soporte para herramientas de ciencia de datos
FROM python:3.10-slim

# Evitar que Python genere archivos .pyc y forzar salida de logs (Sintaxis moderna con '=')
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema (Actualizadas sin paquetes obsoletos)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto y los datos
COPY . .

# Comando por defecto al arrancar el contenedor
CMD ["python", "scripts/dataset_loader.py"]