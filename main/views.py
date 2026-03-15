import os
from heapq import heappush, heappop
import pickle
import requests

from django.shortcuts import render
import wikipedia
from sklearn.feature_extraction.text import TfidfVectorizer
import scipy.sparse
import pandas as pd
import bs4

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from main.models import Article


def index(request):
    if os.path.exists('model.pickle') and os.path.exists('data.npz'):
        return render(request, 'main/index.html')
    return render(request, 'main/need_train.html')


def train(request):
    max_articles_train = int(os.environ.get('num_articles', 1000))
    logger.info(f"Starting training with {max_articles_train} articles")

    Article.objects.all().delete()
    try:
        data = pd.read_csv('wiki_movie_plots_deduped.csv').sample(max_articles_train)
        logger.info(f"Loaded dataset with {len(data)} rows")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return render(request, 'main/error.html')
    text_corpus = list(data.Plot)

    articles = [Article(number=i, title=data.iloc[i].Title[:100], url=data.iloc[i]['Wiki Page'][:100], summary=data.iloc[i].Plot[:4000])
                for i in range(data.shape[0])]

    Article.objects.bulk_create(articles)

    model = TfidfVectorizer(analyzer='word', stop_words='english', strip_accents='ascii')
    param_matrix = model.fit_transform(text_corpus)

    if os.path.exists("model.pickle"):
        os.remove("model.pickle")

    if os.path.exists("data.npz"):
        os.remove("data.npz")

    with open('model.pickle', 'wb') as f:
        pickle.dump(model, f)
    scipy.sparse.save_npz('data.npz', param_matrix)
    logger.info("Model training completed successfully")

    return render(request, 'main/train.html')


def get_similar(request):
    try:
        url = request.GET['url']
        logger.info(f"Processing URL: {url}")

        cnt = int(request.GET['cnt'])
        logger.info(f"Requested count: {cnt}")

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)

        logger.info(f"Response status: {response.status_code}")
        if response.status_code != 200:
            if response.status_code == 404:
                context = {'url': url}
                return render(request, 'main/not_found.html', context)
            else:
                logger.error(f"Wikipedia error {response.status_code}")
                return render(request, 'main/error.html')
    except Exception as e:
        logger.error(f"Exception during get_similar: {e}", exc_info=True)
        return render(request, 'main/error.html')
    if response:
        html = bs4.BeautifulSoup(response.text, 'html.parser')
        heading = html.select("#firstHeading")
        if heading:
            title = heading[0].text
            logger.info(f"Extracted title: {title}")
        else:
            logger.error("No #firstHeading found on page")
            return render(request, 'main/error.html')
        title = html.select("#firstHeading")[0].text
    else:
        context = {'url': url}
        return render(request, 'main/not_found.html', context)
    try:
        page = wikipedia.page(title)
        content = page.content
    except wikipedia.exceptions.PageError as e:
        logger.error(f"Wikipedia page not found: {title}")
        context = {'url': url}
        return render(request, 'main/error.html', context)
    except wikipedia.exceptions.DisambiguationError as e:
        logger.error(f"Disambiguation error for {title}: {e.options[:3]}")
        return render(request, 'main/error.html')
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return render(request, 'main/error.html')
    if not os.path.exists('model.pickle') or not os.path.exists('data.npz'):
        return render(request, 'main/need_train.html')
    with open('model.pickle', 'rb') as model_file:
        model = pickle.load(model_file)
    data = scipy.sparse.load_npz('data.npz')
    film_summary_vector = model.transform([content]).toarray()
    row_number = 0
    top = []
    for row in data:
        vec = row.toarray()
        dist = scipy.spatial.distance.euclidean(vec.reshape(-1), film_summary_vector.reshape(-1))
        heappush(top, (-dist, row_number))
        if len(top) > cnt:
            heappop(top)
        row_number += 1

    top = sorted(top, reverse=True)
    films = []
    for dist, num in top:
        film = Article.objects.get(number=num)
        films.append(film)
    context = {'films': films, 'query_film': page.title}
    return render(request, 'main/get_similar.html', context)
