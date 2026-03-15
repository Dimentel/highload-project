import logging
import os
import pickle
from heapq import heappop, heappush
from pathlib import Path

import bs4
import pandas as pd
import requests
import scipy.sparse
import scipy.spatial
import wikipedia
from celery import shared_task
from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer

from main.models import Article, TaskStatus

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="train_model",
    queue="train_queue",
    autoretry_for=(Exception,),
    retry_kwargs={
        "max_retries": int(os.environ.get("TRAIN_MAX_RETRIES", 3)),
        "countdown": int(os.environ.get("TRAIN_RETRY_DELAY", 60)),
    },
)
def train_model(self, num_articles=None):
    """
    Асинхронная задача для обучения модели
    """
    task_id = self.request.id
    worker_id = f"worker-{self.request.hostname}"

    logger.info(f"[Task {task_id}] Starting model training on {worker_id}")

    if num_articles is None:
        num_articles = int(os.environ.get("NUM_ARTICLES", 1000))
    else:
        num_articles = int(num_articles)
    logger.info(f"Starting training with {num_articles} articles")
    try:
        # Удаляем старые статьи
        Article.objects.all().delete()

        # Загружаем данные
        data = pd.read_csv("wiki_movie_plots_deduped.csv").sample(num_articles)
        text_corpus = list(data.Plot)
        logger.info(f"Loaded dataset with {len(data)} rows")

        # Создаем статьи в БД
        articles = [
            Article(
                number=i,
                title=data.iloc[i].Title[:100],
                url=data.iloc[i]["Wiki Page"][:100],
                summary=data.iloc[i].Plot[:4000],
            )
            for i in range(data.shape[0])
        ]
        Article.objects.bulk_create(articles)

        # Обучаем модель
        model = TfidfVectorizer(analyzer="word", stop_words="english", strip_accents="ascii")
        param_matrix = model.fit_transform(text_corpus)

        base_dir = Path(__file__).resolve().parent.parent
        model_path = base_dir / "model.pickle"
        data_path = base_dir / "data.npz"

        # Удаляем старые файлы
        model_path.unlink(missing_ok=True)
        data_path.unlink(missing_ok=True)

        # Сохраняем модель и данные.
        with model_path.open("wb") as f:
            pickle.dump(model, f)
        scipy.sparse.save_npz(str(data_path), param_matrix)
        logger.info("Model training completed successfully")

        # Обновляем статус задачи
        TaskStatus.objects.filter(task_id=task_id).update(
            status="SUCCESS",
            completed_at=timezone.now(),
            result={"num_articles": num_articles, "message": "Model trained successfully"},
        )

        return {"status": "success", "num_articles": num_articles, "task_id": task_id}

    except Exception as e:
        logger.error(f"Error during training: {e}")
        # Update status in DB
        TaskStatus.objects.filter(task_id=task_id).update(
            status="FAILURE", completed_at=timezone.now(), error_message=str(e)
        )
        raise


@shared_task(
    bind=True,
    name="find_similar",
    queue="similar_queue",
    autoretry_for=(Exception,),
    retry_kwargs={
        "max_retries": int(os.environ.get("SIMILAR_MAX_RETRIES", 2)),
        "countdown": int(os.environ.get("SIMILAR_RETRY_DELAY", 30)),
    },
)
def find_similar(self, url, cnt=5):
    """
    Асинхронная задача для поиска похожих фильмов
    """
    task_id = self.request.id

    logger.info(f"[Task {task_id}] Finding {cnt} similar movies for URL: {url}")

    try:
        # Get content from Wikipedia
        headers = {"User-Agent": "Mozilla/5.0 (Movie Similarity Service)"}
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"Response status: {response.status_code}")

        if response.status_code != 200:
            raise Exception(f"Wikipedia returned status {response.status_code}")

        html = bs4.BeautifulSoup(response.text, "html.parser")
        title = html.select("#firstHeading")[0].text

        # Получаем полный контент страницы
        page = wikipedia.page(title)
        content = page.content

        # Проверяем наличие модели
        if not Path("model.pickle").exists() or not Path("data.npz").exists():
            raise Exception("Model not trained. Please train model first.")

        # Загружаем модель и данные
        with Path("model.pickle").open("rb") as model_file:
            model = pickle.load(model_file)

        data = scipy.sparse.load_npz("data.npz")

        # Векторизуем запрос
        query_vector = model.transform([content]).toarray()

        # Ищем ближайшие векторы
        top = []

        for row_number, row in enumerate(data):
            vec = row.toarray()
            dist = scipy.spatial.distance.euclidean(vec.reshape(-1), query_vector.reshape(-1))
            heappush(top, (-dist, row_number))
            if len(top) > cnt:
                heappop(top)

        # Получаем фильмы из БД
        top = sorted(top, reverse=True)
        films = []
        for _, num in top:
            film = Article.objects.get(number=num)
            films.append(
                {
                    "title": film.title,
                    "url": film.url,
                    "summary": film.summary,
                    "number": film.number,
                }
            )

        # Обновляем статус задачи
        TaskStatus.objects.filter(task_id=task_id).update(
            status="SUCCESS",
            completed_at=timezone.now(),
            result={"query_film": page.title, "films": films, "count": len(films)},
        )

        return {"status": "success", "query_film": page.title, "films": films, "task_id": task_id}

    except Exception as e:
        if isinstance(e, wikipedia.exceptions.PageError):
            logger.error(f"Wikipedia page not found: {e}")
        else:
            logger.error(f"Error during finding similar movies: {e}")
        # Update status in DB
        TaskStatus.objects.filter(task_id=task_id).update(
            status="FAILURE", completed_at=timezone.now(), error_message=str(e)
        )
        raise
