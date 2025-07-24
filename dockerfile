# Usa una imagen oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

COPY requirements.txt /app/
# Copia los archivos necesarios
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

# Instala las dependencias

# Expone el puerto por el que Streamlit sirve
EXPOSE 8501

# Comando para ejecutar la app Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
