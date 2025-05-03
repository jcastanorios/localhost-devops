# Usar una imagen base oficial de Python
FROM python:3.9-slim

# Configuración del directorio de trabajo
WORKDIR /app

# Copiar los archivos de requerimientos e instalar las dependencias
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación al contenedor
COPY . .

# Exponer el puerto en el que Flask se ejecutará
EXPOSE 5000

# Comando para ejecutar la aplicación Flask en modo desarrollo
CMD ["./wait-for-it.sh", "db:5432", "--", "flask", "run", "--host=0.0.0.0"]
