FROM python:3.7-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Копируем проект (исключения - .dockerignore)
COPY . .
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=review2.settings \
    num_articles=1000
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]