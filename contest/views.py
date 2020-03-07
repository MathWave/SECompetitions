from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from contest import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from sqlite3 import connect
from zipfile import ZipFile as zf
from urllib.request import quote


########################################################################################################################

def current_index():
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('SELECT * FROM Solutions')
    amount = len(cursor.fetchall())
    cursor.close()
    connector.close()
    return amount


def solution_info(id):
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('SELECT * FROM Solutions WHERE id = ?', (id,))
    res = cursor.fetchone()
    cursor.close()
    connector.close()
    return {
        'competition': res[1],
        'task': res[2],
        'username': res[3]
    }



########################################################################################################################


# создать шаблон для соревнования
def admin_create_competition_template(name):
    from os.path import exists
    from os import mkdir, system
    if not exists('../competitions'):
        mkdir('../competitions')
    mkdir('../competitions/' + name)
    mkdir('../competitions/' + name + '/tasks')
    mkdir('../competitions/' + name + '/solutions')


# получить список соревнований
def admin_competitions_table():
    from os import listdir, mkdir
    from os.path import exists
    if not exists('../competitions'):
        mkdir('../competitions')
    comps = sorted(listdir('../competitions'))
    line = '<table>\n'
    for c in comps:
        if not c.startswith('.'):
            line += '<tr><td><a href="http://127.0.0.1:8000/admin/competition/' + c + '">' + c + '</td></tr>\n'
    line += '</table>'
    return line


def admin_tasks_table(competition_name):
    from os import listdir
    tasks = sorted(listdir('../competitions/' + competition_name + '/tasks'))
    line = '<table>\n'
    for c in tasks:
        if not c.startswith('.'):
            line += '<tr><td><a href="http://127.0.0.1:8000/admin/task/' + competition_name + '/' + c + '">' + c + '</td></tr>\n'
    line += '</table>'
    return line


def solutions_table(competition_name):
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('SELECT * FROM Solutions WHERE competition = ?', (competition_name,))
    solution_list = cursor.fetchall()
    cursor.close()
    connector.close()
    table = '<tr><td><b>Id</b></td><td><b>Таск</b></td><td><b>Пользователь</b></td></tr>'
    for solution in solution_list:
        table += '<tr>\n'
        table += "<td><a href='http://127.0.0.1:8000/admin/solution/" + str(solution[0]) + "'>" + \
                 str(solution[0]) + '</a>'
        for i in 2, 3:
            table += '<td>' + str(solution[i]) + '</td>\n'
        table += '</tr>\n'
    return table

########################################################################################################################


def admin_show_file(request, id):
    if request.user.is_authenticated and request.user.is_staff:
        info = solution_info(id)
        rootdir = '../competitions/' + info['competition'] + '/solutions/' + info['task'] + '/' + id + '/' + \
                  request.GET.get('file', '')
        file = open(rootdir, 'r').read().replace('\n', '<br>').replace('    ', '&emsp;&emsp;')
        return render(request, 'admin/show_file.html', context={'competition': info['competition'],
                                                                'task': info['task'],
                                                                'username': info['username'],
                                                                'id': id,
                                                                'filename': rootdir.split('/')[-1],
                                                                'text': file
                                                               })
    return HttpResponseRedirect('/enter')


def admin_solution(request, id):
    if request.user.is_authenticated and request.user.is_staff:
        info = solution_info(id)
        files = ''
        from os import listdir
        from os.path import isfile, abspath, isdir
        rootdir = '../competitions/' + info['competition'] + '/solutions/' + info['task'] + '/' + id + '/' + \
                  request.GET.get('folder', '')
        for file in listdir(rootdir):
            files += '<div><img src="'
            a = abspath(file)
            if isfile(rootdir + '/' + file):
                files += 'http://icons.iconarchive.com/icons/icons8/windows-8/16/Very-Basic-Document-icon.png'
                f = '/'.join(rootdir.split('/')[6:])
                files += '">    <a href=http://127.0.0.1:8000/admin/show_file/' + id + '?file=' + \
                         quote('/'.join(rootdir.split('/')[6:]) + '/' + file, safe='') + '>' + file + '</div>\n'
            else:
                files += 'http://icons.iconarchive.com/icons/icons8/ios7/16/Very-Basic-Opened-Folder-icon.png'
                files += '">    <a href=http://127.0.0.1:8000/admin/solution/' + id + '?folder=' + \
                         quote('/'.join(rootdir.split('/')[6:]) + '/' + file, safe='') + '>' + file + '</div>\n'
        return render(request, 'admin/solution.html', context={'competition': info['competition'],
                                                               'task': info['task'],
                                                               'username': info['username'],
                                                               'id': id,
                                                               'files': files
                                                      })
    return HttpResponseRedirect('/enter')


def admin_solutions(request, competition_name):
    if request.user.is_authenticated and request.user.is_staff:
        return render(request, "admin/solutions.html", context={'name': competition_name,
                                                                'solutions': solutions_table(competition_name)})
    return HttpResponseRedirect('/enter')


def admin_new_competition(request):
    if request.user.is_authenticated and request.user.is_staff:
        if request.method == 'GET':
            return render(request, "admin/new_competition.html", context={"form": forms.NewCompetitionForm()})
        else:
            admin_create_competition_template(request.POST.get('name'))
            return HttpResponseRedirect('/admin/main')
    return HttpResponseRedirect('/enter')


def admin_competition(request, name):
    if request.user.is_authenticated and request.user.is_staff:
        return render(request, "admin/competitions_settings.html", context={"name": name,
                                                                            'tasks': admin_tasks_table(name),
                                                                            'solutions': solutions_table(name)})
    else:
        return HttpResponseRedirect('/enter')


def admin_task(request, competition_name, task_name):
    if request.user.is_authenticated and request.user.is_staff:
        fields = ['legend', 'input', 'output']
        context = {}
        for field in fields:
            context[field] = get_info(competition_name, task_name, field)
        from os import listdir
        if len(listdir('../competitions/' + competition_name + '/tasks/' + task_name + '/tests')) > 1:
            context['tests_uploaded'] = True
        else:
            context['tests_uploaded'] = False
        if len(listdir('../competitions/' + competition_name + '/tasks/' + task_name + '/samples')) > 1:
            context['samples_uploaded'] = True
        else:
            context['samples_uploaded'] = False
        context['tests'] = forms.TestsForm()
        context['samples'] = forms.SamplesForm()
        if request.method == 'POST':
            fields = ['input', 'output', 'legend']
            for field in fields:
                write_info(competition_name, task_name, field, request.POST[field])
            folders = [
                'tests',
                'samples'
            ]
            from os import remove, system
            for folder in folders:
                if folder in request.FILES.keys():
                    file = request.FILES[folder]
                    archive = '../competitions/' + competition_name + '/tasks/' + task_name + '/' + folder + '/input.zip'
                    system('touch ' + archive)
                    with open(archive, 'wb+') as fs:
                        for chunk in file.chunks():
                            fs.write(chunk)
                    with zf(archive) as obj:
                        l = archive.split('/')
                        obj.extractall('/'.join(l[0:len(l) - 1]))
                    remove(archive)
            return HttpResponseRedirect('/admin/task/' + competition_name + '/' + task_name)
        return render(request, 'admin/task_settings.html', context=context)
    return HttpResponseRedirect('/enter')


def admin_new_task(request, competition_name):
    if request.user.is_authenticated and request.user.is_staff:
        if request.method == 'GET':
            return render(request, 'admin/new_task.html', context={'form': forms.NewTaskForm(), 'name': competition_name})
        else:
            from os import mkdir, system
            task_name = request.POST['name']
            this_directory = '../competitions/' + competition_name + '/tasks/' + task_name + '/'
            mkdir(this_directory)
            mkdir('../competitions/' + competition_name + '/solutions/' + task_name + '/')
            mkdir(this_directory + 'tests')
            mkdir(this_directory + 'samples')
            system('touch ' + this_directory + 'input.txt')
            system('touch ' + this_directory + 'output.txt')
            system('touch ' + this_directory + 'legend.txt')
            return HttpResponseRedirect('/admin/competition/' + competition_name)
    return HttpResponseRedirect('/enter')


def admin_main(request):
    if request.user.is_authenticated and request.user.is_staff:
        return render(request, "admin/admin.html", context={"competitions": admin_competitions_table()})
    return HttpResponseRedirect('/enter')

########################################################################################################################


def get_samples(competition_name, task_name):
    from os import listdir
    from os.path import isfile, abspath, exists
    folder = '../competitions/' + competition_name + '/tasks/' + task_name + '/samples/'
    html = ''
    count = 1
    while True:
        if not exists(folder + "{:02d}".format(count)):
            break
        html += '<h3>Пример ' + str(count) + '</h3>\n'
        html += '<table width="400">\n<tr><td><h4>Вход</h4>'
        html += open(folder + "{:02d}".format(count), 'r').read() + '</td>\n<td><h4>Выход</h4>\n'
        html += open(folder + "{:02d}".format(count) + '.a', 'r').read() + '</td>\n</tr>\n</table>'
        count += 1
    return html


# получить список всех соревнований (потом надо будет сделать фильтр)
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


# получить таблицу с заданиями из соревнования competition_name
def tasks_table(competition_name):
    from os import listdir
    tasks = listdir('../competitions/' + competition_name + '/tasks')
    line = '<table>\n'
    for c in tasks:
        if not c.startswith('.'):
            line += '<tr><td><a href="http://127.0.0.1:8000/task/' + competition_name + '/' + c + '">' + c + '</td></tr>\n'
    line += '</table>'
    return line


# считать информацию из файла с входными выходными данными или легендой
def get_info(competition_name, task_name, filename):
    return '<br />'.join(open('../competitions/' + competition_name + '/tasks/' + task_name + '/' + filename + '.txt').readlines())


def write_info(competition_name, task_name, filename, text):
    with open('../competitions/' + competition_name + '/tasks/' + task_name + '/' + filename + '.txt', 'w') as fs:
        fs.write(text)


########################################################################################################################


def main(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return render(request, "admin/main.html", context={"competitions": competitions_table()})
        else:
            return render(request, "competitor/main.html", context={"competitions": competitions_table()})
    else:
        return HttpResponseRedirect("/enter")


def redirect(request):
    return HttpResponseRedirect('/main')


def competition(request, name):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return render(request, "admin/competition.html", context={"name": name, 'tasks': tasks_table(name)})
        else:
            return render(request, "competitor/competition.html", context={"name": name, 'tasks': tasks_table(name)})
    else:
        return HttpResponseRedirect('/enter')


def task(request, competition_name, task_name):
    if request.user.is_authenticated:
        if request.method == 'GET':
            context={
                'competition_name': competition_name,
                'task_name': task_name,
                'legend': get_info(competition_name, task_name, 'legend'),
                'input': get_info(competition_name, task_name, 'input'),
                'output': get_info(competition_name, task_name, 'output'),
                'samples': get_samples(competition_name, task_name),
                'form': forms.FileForm()
            }
            if request.user.is_staff:
                return render(request, "admin/task.html", context=context)
            else:
                return render(request, "competitor/task.html", context=context)
        else:
            form = forms.FileForm(request.POST, request.FILES)
            if form.is_valid():
                from os import mkdir, remove, rmdir
                file = request.FILES['file']
                this_directory = '../competitions/' + competition_name + '/solutions/' + task_name + '/'
                index = current_index()
                with open(this_directory + str(index) + '.zip', 'wb') as fs:
                    for chunk in file.chunks():
                        fs.write(chunk)
                from os import remove
                with zf(this_directory + str(index) + '.zip') as obj:
                    obj.extractall(this_directory + str(index) + '/')
                remove(this_directory + str(index) + '.zip')
                connector = connect('db.sqlite3')
                cursor = connector.cursor()
                cursor.execute("INSERT INTO Solutions VALUES (?, ?, ?, ?)", (index, competition_name, task_name, request.user.username))
                connector.commit()
                cursor.close()
                connector.close()
            return HttpResponseRedirect('/task/' + competition_name + '/' + task_name)
    return HttpResponseRedirect('/enter')


def settings(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return render(request, 'admin/settings.html', context={'name': request.user.username})
        else:
            return render(request, "competitor/settings.html", context={"name": request.user.username})
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