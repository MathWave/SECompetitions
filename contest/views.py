from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from contest import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout


########################################################################################################################


def competitions_table():
    from os import listdir, mkdir
    from os.path import exists
    if not exists('../competitions'):
        mkdir('../competitions')
    comps = listdir('../competitions')
    line = '<table>\n'
    for c in comps:
        if not c.startswith('.'):
            line += '<tr><td><a href="http://127.0.0.1:8000/competition/' + c + '">' + c + '</td></tr>\n'
    line += '</table>'
    return line


def tasks_table(competition_name):
    from os import listdir
    tasks = listdir('../competitions/' + competition_name + '/tasks')
    line = '<table>\n'
    for c in tasks:
        if not c.startswith('.'):
            line += '<tr><td><a href="http://127.0.0.1:8000/task/' + competition_name + '/' + c + '">' + c + '</td></tr>\n'
    line += '</table>'
    return line


def get_info(competition_name, task_name, filename):
    return '<br />'.join(open('../competitions/' + competition_name + '/tasks/' + task_name + '/' + filename + '.txt').readlines())


########################################################################################################################


def main(request):
    if request.user.is_authenticated:
        return render(request, "main.html", context={"competitions": competitions_table()})
    else:
        return HttpResponseRedirect("/enter")


def competition(request, name):
    if request.user.is_authenticated:
        return render(request, "competition.html", context={"name": name, 'tasks': tasks_table(name)})
    else:
        return HttpResponseRedirect('/enter')


def task(request, competition_name, task_name):
    if request.user.is_authenticated:
        if request.method == 'GET':
            return render(request, "task.html", context={
                'competition_name': competition_name,
                'task_name': task_name,
                'legend': get_info(competition_name, task_name, 'legend'),
                'input': get_info(competition_name, task_name, 'input'),
                'output': get_info(competition_name, task_name, 'output'),
                'form': forms.FileForm()
            })
        else:
            form = forms.FileForm(request.POST, request.FILES)
            if form.is_valid():
                from os import mkdir, remove, rmdir
                file = request.FILES['file']
                this_directory = '../competitions/' + competition_name + '/solutions/' + task_name + '/'
                with open(this_directory + request.user.username + '.zip', 'wb') as fs:
                    for chunk in file.chunks():
                        fs.write(chunk)
            return HttpResponseRedirect('/task/' + competition_name + '/' + task_name)
    return HttpResponseRedirect('/enter')


def settings(request):
    if request.user.is_authenticated:
        return render(request, "settings.html", context={"name": request.user.username})
    else:
        return HttpResponseRedirect("/enter")


def restore(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/main")
    else:
        return render(request, "restore.html")


def enter(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/main")
    if request.method == "POST":
        user = authenticate(username=request.POST.get('email'), password=request.POST.get('password'))
        if user is not None and user.is_active:
            login(request, user)
            request.session["is_auth_ok"] = '1'
            if request.POST.get('email') == 'admin':
                return HttpResponseRedirect('/admin')
            return HttpResponseRedirect('/main')
        else:
            return HttpResponseRedirect('/enter')
    else:
        loginform = forms.LoginForm()
        return render(request, "enter.html", context={"form": loginform})


def exit(request):
    logout(request)
    request.session["is_auth_ok"] = '0'
    return HttpResponseRedirect('/enter')


def create_user(request, username, password):
    User.objects.create_user(username=username, password=password)
    return HttpResponse("OK")


# ======================================================================================================================
# ======================================================================================================================