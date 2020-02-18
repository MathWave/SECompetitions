from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from contest import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout


def check_admin(request):
    return request.user.is_authenticated and request.user.username == 'admin'


def main(request):
    if request.user.is_authenticated:
        return render(request, "main.html", context={"name": request.user.username})
    else:
        return HttpResponseRedirect("/enter")


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