# Movie Similarity Service (Python review 2 Django web service)
Сервис для поиска похожих фильмов по сюжетам из Wikipedia.
## Особенности
- Поиск похожих фильмов по тексту сюжета с использованием TF-IDF
- Веб-интерфейс для ввода URL Wikipedia страницы
- Использование PostgreSQL для хранения данных
- Docker Compose для простого развертывания

## Необходимые пакеты
    - django (легко устанавливается с помощью pip)
    - pickle
    - wikipedia (так же устанавливается с помощью pip)
    - numpy, scipy, pandas, sklearn
    - bs4
    - requests

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
Должны быть запущены два сервиса: similar_movies_db и similar_movies_app   

**4. Инициализируйте данные:**  
- Откройте в браузере http://localhost:8000/train/.
- Дождитесь завершения обучения модели (загрузка датасета и обучение TF-IDF).
- После обучения вы увидите сообщение "Model trained!"

**5. Поиск похожих фильмов:**  
- Перейдите на главную страницу: http://localhost:8000/.  
- Введите URL Wikipedia страницы фильма (например: https://en.wikipedia.org/wiki/Inception).  
- Выберите количество похожих фильмов для поиска (5, 10, 15, 20).

**Конфигурация**  
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
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Application settings
num_articles=1000
PYTHONUNBUFFERED=1

# Database URL
DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}
   ```
**Управление контейнерами**
   ```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f web
docker-compose logs -f db

# Пересборка образа
docker-compose build

# Полная переустановка (с удалением данных)
docker-compose down -v
docker-compose up -d
   ```

### Без Docker
Находясь в папке с файлом manage.py (корневой каталог репозитория) выполняем действия.
**1. Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
**2. Настройте базу данных (SQLite по умолчанию):**
   ```bash
   python manage.py migrate
   ```
**3. Запустите сервер:**
   ```bash
   python manage.py runserver
   ```
Шаги 4-5 такие же, как при запуске с Docker.

    