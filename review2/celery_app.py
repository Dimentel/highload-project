import os
from celery import Celery
from celery.signals import task_failure, task_success, task_retry
import requests

# Установка настроек Django по умолчанию для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'review2.settings')

# Создаем экземпляр Celery
celery_app = Celery('review2')

# Загружаем конфигурацию из Django settings
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в приложениях Django
celery_app.autodiscover_tasks()


# Обработчики сигналов для обновления статуса в БД
@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Обновляем статус задачи при успешном завершении"""
    task_id = sender.request.id
    task_name = sender.name

    print(f"=== task_success_handler called for {task_name} ===")
    print(f"task_id: {task_id}")

    try:
        # Отправляем запрос к API для обновления статуса
        api_url = os.environ.get('API_URL', 'http://web:8000')
        url = f"{api_url}/tasks/status/"
        print(f"Sending to URL: {url}")

        response = requests.post(
            url,
            json={
                'task_id': task_id,
                'status': 'SUCCESS',
                'result': result,
                'task_name': task_name
            },
            timeout=5
        )
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    except Exception as e:
        print(f"Failed to update task status: {e}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None,
                         **kw):
    """Обновляем статус задачи при ошибке"""
    try:
        api_url = os.environ.get('API_URL', 'http://web:8000')
        requests.post(
            f"{api_url}/tasks/status/",
            json={
                'task_id': task_id,
                'status': 'FAILURE',
                'error': str(exception),
                'task_name': sender.name if sender else 'unknown'
            },
            timeout=5
        )
    except Exception as e:
        print(f"Failed to update task status: {e}")


@task_retry.connect
def task_retry_handler(sender=None, request=None, reason=None, einfo=None, **kwargs):
    """Обновляем статус задачи при повторной попытке"""
    task_id = request.id if request else None

    try:
        api_url = os.environ.get('API_URL', 'http://web:8000')
        requests.post(
            f"{api_url}/tasks/status/",
            json={
                'task_id': task_id,
                'status': 'RETRY',
                'error': str(reason) if reason else None,
                'task_name': sender.name if sender else 'unknown'
            },
            timeout=5
        )
    except Exception as e:
        print(f"Failed to update task status: {e}")
