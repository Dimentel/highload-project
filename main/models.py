import uuid

from django.db import models


class Article(models.Model):
    number = models.IntegerField()
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    summary = models.CharField(max_length=5000)


class TaskStatus(models.Model):
    """Модель для отслеживания статуса асинхронных задач"""

    TASK_TYPES = (
        ("train", "Обучение модели"),
        ("similar", "Поиск похожих фильмов"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Ожидает"),
        ("STARTED", "Выполняется"),
        ("SUCCESS", "Успешно завершено"),
        ("FAILURE", "Ошибка"),
        ("RETRY", "Повторная попытка"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.CharField(max_length=255, db_index=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    # Параметры задачи
    params = models.JSONField(default=dict, blank=True)
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True, default="")

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Метаданные
    worker_id = models.CharField(max_length=100, blank=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task_type} - {self.task_id[:8]} - {self.status}"
