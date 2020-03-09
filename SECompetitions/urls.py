from django.contrib import admin
from django.urls import path, re_path
from contest import views

urlpatterns = [
    path('main', views.main),
    path('settings', views.settings),
    path('enter', views.enter),
    path('restore', views.restore),
    path('exit', views.exit),
    path('competition/<name>', views.competition),
    path('task/<competition_name>/<task_name>', views.task),

    path('admin/new_competition', views.admin_new_competition),
    path('admin/competition/<name>', views.admin_competition),
    path('admin/task/<competition_name>/<task_name>', views.admin_task),
    path('admin/new_task/<competition_name>', views.admin_new_task),
    path('admin/main', views.admin_main),
    path('admin/solutions/<competition_name>', views.admin_solutions),
    path('admin/solution/<id>', views.admin_solution),
    path('admin/show_file/<id>', views.admin_show_file),
    path('admin/delete_competition/<competition_name>', views.admin_delete_competition),
    path('admin/delete_task/<competition_name>/<task_name>', views.admin_delete_task),

    path('create_user/<username>/<password>', views.create_user),
    re_path('^', views.redirect)
]
