# Это гарантирует, что Celery будет загружен при старте Django
from .celery_app import celery_app

__all__ = ("celery_app",)
