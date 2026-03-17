# Movie Similarity Service

Сервис для поиска похожих фильмов по сюжетам из Wikipedia с асинхронной
обработкой задач.

## Особенности

- Поиск похожих фильмов по тексту сюжета с использованием TF-IDF
- Асинхронная обработка через Celery + RabbitMQ
- Production-окружение с Nginx (reverse proxy + статика)
- PostgreSQL для хранения данных и статусов задач
- Мониторинг через Flower
- Полная контейнеризация с Docker Compose
- Поддержка Kubernetes (развертывание в Minikube или полноценном кластере)

## Запускаем сервер

### С Docker Compose

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

Должны быть запущены все сервисы:

- similar_movies_reverse_proxy - Nginx (порт 80)
- similar_movies_static - Nginx для статики
- similar_movies_app - Django + Gunicorn
- similar_movies_celery - Celery worker
- similar_movies_rmq - RabbitMQ
- similar_movies_db - PostgreSQL
- similar_movies_flower - Flower мониторинг

**4. Инициализируйте данные:**

- Откройте в браузере http://localhost:8000/train/.
- Нажмите "Start Training" и дождитесь завершения
- Статус обучения можно отслеживать на той же странице

**5. Поиск похожих фильмов:**

- Перейдите на главную страницу: http://localhost:/.
- Введите URL Wikipedia страницы фильма (например:
  https://en.wikipedia.org/wiki/Inception).
- Выберите количество похожих фильмов для поиска (5, 10, 15, 20) и нажмите
  "Search".
- Результаты появятся после завершения обработки

### Развертывание в Kubernetes (Minikube)

**Предварительные требования:**

- Установленный Minikube и kubectl
- Linux (рекомендуется) или macOS
- репозиторий склонирован и текущая папка - папка проекта

**Запустите Minikube:**

- minikube start --driver=docker
- minikube addons enable ingress

**1. Создайте namespace и примените конфигурации**

kubectl apply -f namespace.yaml kubectl apply -f configmap.yaml kubectl apply -f
secrets.yaml

Создайте секрет для доступа к Docker registry (замените токен): kubectl create
secret docker-registry registrysecret \
 --docker-server=registry.gitlab.akhcheck.ru \
 --docker-username=dmitrii.boldyrev \
 --docker-password=<ваш_токен> \
 --docker-email=daboldyrev@edu.hse.ru \
 -n hl-project

Примените остальные манифесты: kubectl apply -f pvc/ kubectl apply -f
statefulset/ kubectl apply -f job/ kubectl apply -f deployment/ kubectl apply -f
service/ kubectl apply -f ingress.yaml

Можно выполнить одну команду ./deploy.bash

**2. Дождитесь запуска всех подов:** ubectl get pods -n hl-project -w

**3. Добавьте запись в /etc/hosts (на Linux):** echo "$(minikube ip)
hl-project.test" | sudo tee -a /etc/hosts

Доступ к сервисам Kubernetes Приложение: http://hl-project.test Flower
мониторинг: http://hl-project.test:5555 RabbitMQ management:
http://hl-project.test:15672 (логин: student, пароль: qwerty)

**Управление кластером:**

# Просмотр статуса подов

kubectl get pods -n hl-project

# Логи приложения

kubectl logs -n hl-project -l app=web

# Перезапуск подов

kubectl delete pod -n hl-project -l app=web

# Удаление всех ресурсов

kubectl delete -f k8s/ **Конфигурация:** Файл .env содержит настройки (создайте
если отсутствует):

```bash
# Database
DB_USER=similar_user
DB_PASS=similar_pass
DB_NAME=similar_movies
DB_HOST=db
DB_PORT=5432

# Django development secret key - development-secret-key-change-in-production
DJANGO_SETTINGS_MODULE=review2.settings
DJANGO_SECRET_KEY=production-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,nginx,web

# Application settings
NUM_ARTICLES=1000
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

# Static files
STATIC_URL=/static/
STATIC_ROOT=/app/staticfiles
STATICFILES_STORAGE=whitenoise.storage.CompressedManifestStaticFilesStorage

# Gunicorn
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120

REGISTRY_TOKEN=your-token
```

**Примечания для разработчиков**

- Docker Compose — для локальной разработки
- Kubernetes — для production-развертывания На Linux все работает "из коробки",
  на Windows возможны проблемы с Minikube (доступ к клсастеру) даже с WSL2.
