# Movie Similarity Service
Сервис для поиска похожих фильмов по сюжетам из Wikipedia с асинхронной обработкой задач.
## Особенности
- Поиск похожих фильмов по тексту сюжета с использованием TF-IDF
- Асинхронная обработка через Celery + RabbitMQ
- Веб-интерфейс для ввода URL Wikipedia страницы
- Использование PostgreSQL для хранения данных
- Мониторинг через Flower
- Docker Compose для простого развертывания

## Запускаем сервер
### С Docker Compose (рекомендуется)
**1. Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd highload-project
   ``` 
**2. Запустите проект:**
   ```bash
   docker-compose up -d
   ```
**3. Проверьте статус:**
   ```bash
   docker-compose ps
   ```
Должны быть запущены: similar_movies_db, similar_movies_app, similar_movies_celery, similar_movies_rmq, similar_movies_flower   

**4. Инициализируйте данные:**  
- Откройте в браузере http://localhost:8000/train/.
- Нажмите "Start Training" и дождитесь завершения
- Статус обучения можно отслеживать на той же странице

**5. Поиск похожих фильмов:**  
- Перейдите на главную страницу: http://localhost:8000/.  
- Введите URL Wikipedia страницы фильма (например: https://en.wikipedia.org/wiki/Inception).  
- Выберите количество похожих фильмов для поиска (5, 10, 15, 20) и нажмите "Search".
- Результаты появятся после завершения обработки

**Мониторинг:**  
- Flower: http://localhost:5555 — мониторинг Celery задач  
- RabbitMQ: http://localhost:15672 (логин: student, пароль: qwerty)

**Конфигурация:**  
Файл .env содержит настройки (создайте если отсутствует):
   ```bash
# Database
DB_USER=similar_user
DB_PASS=similar_pass
DB_NAME=similar_movies
DB_HOST=db
DB_PORT=5432

# Django
DJANGO_SETTINGS_MODULE=review2.settings
DJANGO_SECRET_KEY=development-secret-key-change-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,web

# Application settings
num_articles=1000
PYTHONUNBUFFERED=1

# Database URL
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# RabbitMQ
RABBITMQ_HOST=rmq
RABBITMQ_PORT=5672
RABBITMQ_USER=student
RABBITMQ_PASSWORD=qwerty
RABBITMQ_MANAGEMENT_PORT=15672

# Celery
CELERY_BROKER_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@${RABBITMQ_HOST}:${RABBITMQ_PORT}//
CELERY_RESULT_BACKEND=rpc://
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_WORKER_CONCURRENCY=3
CELERY_TASK_TRACK_STARTED=True
CELERY_TASK_ACKS_LATE=True
CELERY_TASK_REJECT_ON_WORKER_LOST=True
CELERY_TASK_RETRY_DELAY=300
CELERY_TASK_MAX_RETRIES=3
TRAIN_MAX_RETRIES=3
TRAIN_RETRY_DELAY=60
SIMILAR_MAX_RETRIES=2
SIMILAR_RETRY_DELAY=30
CELERY_WORKER_PREFETCH_MULTIPLIER=4

# Queues
TRAIN_QUEUE=train_queue
SIMILAR_QUEUE=similar_queue

# API URLs
API_URL=http://web:8000
UPDATE_TASK_STATUS_URL=${API_URL}/tasks/status/

# Timeouts
TRAIN_TIMEOUT=300
SIMILAR_TIMEOUT=60
```