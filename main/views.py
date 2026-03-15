import json
import logging
import os

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from main.models import Article, TaskStatus
from main.tasks import find_similar, train_model

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def index(request):
    if Article.objects.exists():
        return render(request, "main/index.html")
    return render(request, "main/need_train.html")


@csrf_exempt
def train(request):
    """
    Асинхронное обучение модели
    """
    if request.method == "POST":
        # Создаем задачу
        num_articles = request.POST.get("NUM_ARTICLES", os.environ.get("NUM_ARTICLES", 1000))

        # Отправляем задачу в Celery и сразу получаем её ID
        result = train_model.delay(int(num_articles))
        celery_task_id = result.id

        # Make a record in the database
        task = TaskStatus.objects.create(
            task_type="train",
            task_id=celery_task_id,
            status="PENDING",
            params={"num_articles": int(num_articles)},
        )

        return JsonResponse(
            {"task_id": str(task.id), "status": "PENDING", "message": "Training task created"}
        )

    # GET запрос - показываем форму
    return render(request, "main/train_form.html")


@csrf_exempt
def get_similar(request):
    """
    Асинхронный поиск похожих фильмов
    """
    if request.method == "POST":
        data = json.loads(request.body)
        url = data.get("url")
        cnt = data.get("cnt", 5)

        if not url:
            return JsonResponse({"error": "URL is required"}, status=400)

        # Отправляем задачу
        result = find_similar.delay(url, cnt)
        celery_task_id = result.id

        # Make a record in the database
        task = TaskStatus.objects.create(
            task_type="similar",
            task_id=celery_task_id,
            status="PENDING",
            params={"url": url, "cnt": cnt},
        )

        return JsonResponse(
            {
                "task_id": str(task.id),
                "status": "PENDING",
                "message": "Similarity search task created",
            }
        )

    # GET запрос - показываем форму
    return render(request, "main/index.html")


def task_status(request, task_id):
    """
    Получение статуса задачи
    """
    try:
        # Пытаемся найти задачу по нашему ID или по Celery task_id
        task = TaskStatus.objects.get(id=task_id)
    except TaskStatus.DoesNotExist:
        try:
            task = TaskStatus.objects.get(task_id=task_id)
        except TaskStatus.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)

    response = {
        "task_id": str(task.id),
        "celery_task_id": task.task_id,
        "task_type": task.task_type,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }

    if task.status == "SUCCESS":
        response["result"] = task.result
    elif task.status == "FAILURE":
        response["error"] = task.error_message

    return JsonResponse(response)


def task_result(request, task_id):
    """
    Получение результата задачи (если завершена)
    """
    try:
        task = TaskStatus.objects.get(id=task_id)
    except TaskStatus.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)

    if task.status == "SUCCESS":
        return JsonResponse({"task_id": str(task.id), "status": task.status, "result": task.result})
    if task.status == "FAILURE":
        return JsonResponse(
            {"task_id": str(task.id), "status": task.status, "error": task.error_message},
            status=400,
        )
    return JsonResponse(
        {
            "task_id": str(task.id),
            "status": task.status,
            "message": "Task is not completed yet",
        },
        status=202,
    )


@csrf_exempt
def update_task_status(request):
    """
    Эндпоинт для обратной связи от Celery worker (через сигналы)
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        task_id = data.get("task_id").lower()
        status = data.get("status")
        result = data.get("result")
        error = data.get("error")

        logger.info("=== update_task_status called ===")
        logger.info(f"Looking for task with task_id={task_id}")

        # Обновляем статус задачи
        task = TaskStatus.objects.filter(task_id=task_id).first()
        logger.info(f"Found by task_id: {task.id if task else 'None'}")

        if not task:
            # Если не нашли, посмотрим все задачи
            all_tasks = TaskStatus.objects.all().values("id", "task_id", "status")
            logger.info(f"Looking for {task_id}")
            logger.info(f"All task_ids: {[t['task_id'] for t in all_tasks]}")

            return JsonResponse({"status": "not_found"}, status=404)

        if task:
            logger.info(f"Updating task {task.id} from {task.status} to {status}")
            task.status = status
            if status == "STARTED":
                task.started_at = timezone.now()
                task.worker_id = data.get("worker_id", "")
            elif status == "SUCCESS":
                task.completed_at = timezone.now()
                task.result = result
            elif status == "FAILURE":
                task.completed_at = timezone.now()
                task.error_message = error or ""
            elif status == "RETRY":
                task.retry_count += 1

            task.save()

            return JsonResponse({"status": "updated"})
        # Логируем, но не создаём новую запись
        logger.warning(f"Task {task_id} not found")
        return JsonResponse({"status": "not_found"}, status=404)

    except Exception as e:
        logger.error(f"Error updating task status: {e}")
        return JsonResponse({"error": str(e)}, status=500)
