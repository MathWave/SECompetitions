from django.contrib import admin
from django.urls import path
from contest import views

urlpatterns = [
    path('main', views.main),
    path('settings', views.settings),
    path('enter', views.enter),
    path('restore', views.restore),
    path('exit', views.exit),
    path('create_user/<username>/<password>', views.create_user),
    path('', views.main)
]
