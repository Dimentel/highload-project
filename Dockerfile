FROM python:3.7-slim

# Установка netcat для проверки доступности PostgreSQL
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Копируем проект (исключения - .dockerignore)
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
# Оставим для совместимости с предыдущими версиями
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
