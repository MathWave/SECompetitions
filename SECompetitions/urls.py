from django.contrib import admin
from django.urls import path
from contest import views

urlpatterns = [
    path('main', views.main),
    path('settings', views.settings),
    path('enter', views.enter),
    path('restore', views.restore),
    path('exit', views.exit),
    path('competition/<name>', views.competition),
    path('task/<competition_name>/<task_name>', views.task),
    path('create_user/<username>/<password>', views.create_user),
    path('', views.main)
]
