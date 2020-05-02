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
    path('block', views.block),
    path('task', views.task),

    path('admin/new_block', views.new_block),
    path('admin/block', views.block_settings),
    path('admin/task', views.task_settings),
    path('admin/new_task', views.new_task),
    path('admin/main', views.admin),
    path('admin/solutions', views.solutions),
    path('admin/solution', views.solution),
    path('admin/show_file', views.show_file),
    path('admin/delete_block', views.delete_block),
    path('admin/delete_task', views.delete_task),
    path('admin/remove_tests', views.remove_tests),
    path('admin/users_settings', views.users_settings),
    path('admin/unsubscribe', views.unsubscribe),

    path('superuser/main', views.superuser),
    path('delete_user', views.delete_user),
    path('delete_course', views.delete_course),

    path('reset', views.reset),
    re_path('^', views.redirect)
]
