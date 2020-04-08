from django.contrib import admin
from django.urls import path, re_path
from contest import views

urlpatterns = [
    path('main', views.main),
    path('settings', views.settings),
    path('enter', views.enter),
    path('restore', views.restore),
    path('exit', views.exit),
    path('competition', views.competition),
    path('task', views.task),

    path('admin/new_competition', views.admin_new_competition),
    path('admin/competition', views.admin_competition),
    path('admin/task', views.admin_task),
    path('admin/new_task', views.admin_new_task),
    path('admin/main', views.admin_main),
    path('admin/solutions', views.admin_solutions),
    path('admin/solution', views.admin_solution),
    path('admin/show_file', views.admin_show_file),
    path('admin/delete_competition', views.admin_delete_competition),
    path('admin/delete_task', views.admin_delete_task),
    path('admin/remove_tests', views.admin_remove_tests),

    path('superuser/main', views.superuser),

    path('create_user/<username>/<password>', views.create_user),
    path('reset', views.reset),
    re_path('^', views.redirect)
]
