from django.contrib import admin
from django.urls import path, re_path
from contest import views

urlpatterns = [
    path('main', views.main),
    path('settings', views.settings),
    path('enter', views.enter),
    path('registration', views.registration),
    path('restore', views.restore),
    path('reset_password', views.reset_password),
    path('exit', views.exit),
    path('competition', views.competition),
    path('task', views.task),

    path('admin/new_competition', views.new_competition),
    path('admin/competition', views.competition_settings),
    path('admin/task', views.task_settings),
    path('admin/new_task', views.new_task),
    path('admin/main', views.admin),
    path('admin/solutions', views.solutions),
    path('admin/solution', views.solution),
    path('admin/show_file', views.show_file),
    path('admin/delete_competition', views.delete_competition),
    path('admin/delete_task', views.delete_task),
    path('admin/remove_tests', views.remove_tests),

    path('superuser/main', views.superuser),
    path('delete_user', views.delete_user),

    path('reset', views.reset),
    re_path('^', views.redirect)
]
