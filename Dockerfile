FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear directorio de datos
RUN mkdir -p data

# Exponer puerto del webhook
EXPOSE 8080

# Ejecutar bot
CMD ["python", "bot.py"]
