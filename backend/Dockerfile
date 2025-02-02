# Usar una imagen base de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos del proyecto al contenedor
COPY . /app

# Instalar las dependencias necesarias (incluyendo las del archivo requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 5000, ya que Flask correrá en ese puerto
EXPOSE 5000

# Comando para ejecutar el script de indexación y luego iniciar la aplicación Flask
CMD ["bash", "-c", "python app.py && flask run --host=0.0.0.0"]
