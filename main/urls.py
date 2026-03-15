from django.urls import path

from . import views

app_name = 'main'
urlpatterns = [
    path('', views.index, name='index'),
    path('train/', views.train, name='train'),
    path('similar/', views.get_similar, name='similar'),
    path('tasks/<uuid:task_id>/status/', views.task_status, name='task_status'),
    path('tasks/<uuid:task_id>/result/', views.task_result, name='task_result'),
    path('tasks/status/', views.update_task_status, name='update_task_status'),
]
