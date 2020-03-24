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
from threading import Thread


########################################################################################################################

def check_login(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/enter')


def check_admin(request):
    check_login(request)
    if not request.user.is_staff:
        return HttpResponseRedirect('/enter')


def current_index():
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('SELECT * FROM Solutions')
    full = cursor.fetchall()
    number = 0 if len(full) == 0 else full[-1][0] + 1
    cursor.close()
    connector.close()
    return number


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
        'username': res[3],
        'verdict': res[4]
    }


def test(competition_name, task_name, index, connector, cursor):
    from contest.Tester import Tester
    thread = Tester(competition_name, task_name, index)
    thread.start()
    thread.join(5)
    cursor.execute('SELECT * FROM Solutions WHERE id = ?', (index,))
    if cursor.fetchone()[4] == 'TESTING':
        cursor.execute("UPDATE Solutions SET result = 'Time limit' WHERE id = ?;", (index,))
    connector.commit()
    cursor.close()
    connector.close()


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
            line += '<tr><td><a href="http://127.0.0.1:8000/admin/task/' + competition_name + '/' + c + '">' + c + \
                    '</td></tr>\n'
    line += '</table>'
    return line


def solutions_table(competition_name):
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('SELECT * FROM Solutions WHERE competition = ?', (competition_name,))
    solution_list = cursor.fetchall()
    cursor.close()
    connector.close()
    table = '<tr><td><b>Id</b></td><td><b>Соревнование</b></td><td><b>Таск</b></td><td><b>Пользователь</b></td><td><b>Вердикт</b></td></tr>'
    for solution in reversed(solution_list):
        table += '<tr>\n'
        table += "<td><a href='http://127.0.0.1:8000/admin/solution/" + str(solution[0]) + "'>" + \
                 str(solution[0]) + '</a></td>'
        for i in range(1, 5):
            table += '<td>' + str(solution[i]) + '</td>\n'
        table += '</tr>\n'
    return table

########################################################################################################################


def admin_delete_task(request, competition_name, task_name):
    check_admin(request)
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('DELETE FROM Solutions WHERE competition = ? AND task = ?', (competition_name, task_name, ))
    connector.commit()
    cursor.close()
    connector.close()
    from os import system
    system('rm -r ../competitions/' + competition_name + '/tasks/' + task_name)
    system('rm -r ../competitions/' + competition_name + '/solutions/' + task_name)
    return HttpResponseRedirect('/admin/competition/' + competition_name)


def admin_delete_competition(request, competition_name):
    check_admin(request)
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('DELETE FROM Solutions WHERE competition = ?', (competition_name, ))
    connector.commit()
    cursor.close()
    connector.close()
    from os import system
    system('rm -r ../competitions/' + competition_name)
    return HttpResponseRedirect('/admin/main')


def admin_remove_tests(request, competition_name, task_name):
    check_admin(request)
    from os import system, mkdir
    system('rm -r ../competitions/' + competition_name + '/tasks/' + task_name + '/tests')
    mkdir('../competitions/' + competition_name + '/tasks/' + task_name + '/tests')
    return HttpResponseRedirect('/admin/task/' + competition_name + '/' + task_name)


def admin_show_file(request, id):
    check_admin(request)
    info = solution_info(id)
    rootdir = '../competitions/' + info['competition'] + '/solutions/' + info['task'] + '/' + id + '/' + \
              request.GET.get('file', '')
    file = open(rootdir, 'r').read()
    return render(request, 'admin/show_file.html', context={'competition': info['competition'],
                                                            'task': info['task'],
                                                            'username': info['username'],
                                                            'id': id,
                                                            'filename': rootdir.split('/')[-1],
                                                            'verdict': info['verdict'],
                                                            'text': file
                                                           })


def admin_solution(request, id):
    check_admin(request)
    folder = request.GET.get('folder', '')
    if '..' in folder:
        return HttpResponseRedirect('/enter')
    info = solution_info(id)
    files = ''
    from os import listdir
    from os.path import isfile, abspath, isdir
    rootdir = '../competitions/' + info['competition'] + '/solutions/' + info['task'] + '/' + id + '/' + \
              request.GET.get('folder', '')
    for file in sorted(listdir(rootdir)):
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
                                                           'verdict': info['verdict'],
                                                           'files': files
                                                  })


def admin_solutions(request, competition_name):
    check_admin(request)
    return render(request, "admin/solutions.html", context={'name': competition_name,
                                                            'solutions': solutions_table(competition_name)})


def admin_new_competition(request):
    check_admin(request)
    if request.method == 'GET':
        return render(request, "admin/new_competition.html", context={"form": forms.NewCompetitionForm()})
    else:
        admin_create_competition_template(request.POST.get('name'))
        return HttpResponseRedirect('/admin/competition/' + request.POST.get('name'))


def admin_competition(request, name):
    check_admin(request)
    return render(request, "admin/competitions_settings.html", context={"name": name,
                                                                        'tasks': admin_tasks_table(name)})


def admin_task(request, competition_name, task_name):
    check_admin(request)
    fields = ['legend', 'input', 'output', 'specifications']
    context = {
        'competition': competition_name,
        'task': task_name
    }
    for field in fields:
        context[field] = get_info(competition_name, task_name, field)
    from os import listdir
    if len(listdir('../competitions/' + competition_name + '/tasks/' + task_name + '/tests')) != 0:
        context['tests_uploaded'] = True
    else:
        context['tests_uploaded'] = False
    context['tests'] = forms.TestsForm()
    if request.method == 'POST':
        for field in fields:
            write_info(competition_name, task_name, field, request.POST[field])
        from os import remove, system
        if 'tests' in request.FILES.keys():
            file = request.FILES['tests']
            archive = '../competitions/' + competition_name + '/tasks/' + task_name + '/tests/input.zip'
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


def admin_new_task(request, competition_name):
    check_admin(request)
    if request.method == 'GET':
        return render(request, 'admin/new_task.html', context={'form': forms.NewTaskForm(),
                                                               'name': competition_name})
    else:
        from os import mkdir, system
        task_name = request.POST['name']
        this_directory = '../competitions/' + competition_name + '/tasks/' + task_name + '/'
        mkdir(this_directory)
        mkdir('../competitions/' + competition_name + '/solutions/' + task_name + '/')
        mkdir(this_directory + 'tests')
        system('touch ' + this_directory + 'input.txt')
        system('touch ' + this_directory + 'output.txt')
        system('touch ' + this_directory + 'legend.txt')
        system('touch ' + this_directory + 'specifications.txt')
        return HttpResponseRedirect('/admin/task/' + competition_name + '/' + task_name)


def admin_main(request):
    check_admin(request)
    return render(request, "admin/admin.html", context={"competitions": admin_competitions_table()})

########################################################################################################################


# получить список всех соревнований (потом надо будет сделать фильтр)
def competitions_table():
    from os import listdir, mkdir
    from os.path import exists
    if not exists('../competitions'):
        mkdir('../competitions')
    comps = sorted(listdir('../competitions'))
    line = '<table>\n'
    for c in comps:
        if not c.startswith('.'):
            line += '<tr><td><a href="http://127.0.0.1:8000/competition/' + c + '">' + c + '</td></tr>\n'
    line += '</table>'
    return line


# получить таблицу с заданиями из соревнования competition_name
def tasks_table(competition_name):
    from os import listdir
    tasks = sorted(listdir('../competitions/' + competition_name + '/tasks'))
    line = '<table>\n'
    for c in tasks:
        if not c.startswith('.'):
            line += '<tr><td><a href="http://127.0.0.1:8000/task/' + competition_name + '/' + c + '">' + c + \
                    '</td></tr>\n'
    line += '</table>'
    return line


def task_solutions_table(username, competition_name, task_name):
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('SELECT * FROM Solutions WHERE competition = ? AND task = ? AND username = ?', (competition_name, task_name, username))
    solution_list = cursor.fetchall()
    cursor.close()
    connector.close()
    table = '<tr><td><b>Id</b></td><td><b>Соревнование</b></td><td><b>Таск</b></td><td><b>Вердикт</b></td></tr>'
    for solution in reversed(solution_list):
        table += '<tr>\n'
        for i in 0, 1, 2, 4:
            table += '<td>' + str(solution[i]) + '</td>\n'
        table += '</tr>\n'
    return table


# считать информацию из файла с входными выходными данными или легендой
def get_info(competition_name, task_name, filename):
    return '<br />'.join(open('../competitions/' + competition_name + '/tasks/' + task_name + '/' + filename + '.txt')
                         .readlines())


def write_info(competition_name, task_name, filename, text):
    with open('../competitions/' + competition_name + '/tasks/' + task_name + '/' + filename + '.txt', 'w') as fs:
        fs.write(text)


########################################################################################################################


def main(request):
    check_login(request)
    if request.user.is_staff:
        return render(request, "admin/main.html", context={"competitions": competitions_table()})
    else:
        return render(request, "competitor/main.html", context={"competitions": competitions_table()})


def redirect(request):
    return HttpResponseRedirect('/main')





def competition(request, name):
    check_login(request)
    if request.user.is_staff:
        return render(request, "admin/competition.html", context={"name": name, 'tasks': tasks_table(name)})
    else:
        return render(request, "competitor/competition.html", context={"name": name, 'tasks': tasks_table(name)})


def task(request, competition_name, task_name):
    check_login(request)
    if request.method == 'GET':
        context = {
            'competition_name': competition_name,
            'task_name': task_name,
            'legend': get_info(competition_name, task_name, 'legend'),
            'input': get_info(competition_name, task_name, 'input'),
            'output': get_info(competition_name, task_name, 'output'),
            'specifications': get_info(competition_name, task_name, 'specifications'),
            'form': forms.FileForm(),
            'solutions': task_solutions_table(request.user.username, competition_name, task_name)
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
            cursor.execute("INSERT INTO Solutions VALUES (?, ?, ?, ?, ?)", (index,
                                                                         competition_name,
                                                                         task_name,
                                                                         request.user.username,
                                                                            'TESTING'))
            connector.commit()
            cursor.close()
            connector.close()
            from contest.TesterGlobal import TesterGlobal
            TesterGlobal(competition_name, task_name, index, 3000).start()
        return HttpResponseRedirect('/task/' + competition_name + '/' + task_name)


def settings(request):
    check_login(request)
    if request.user.is_staff:
        return render(request, 'admin/settings.html', context={'name': request.user.username})
    else:
        return render(request, "competitor/settings.html", context={"name": request.user.username})


def restore(request):
    check_login(request)
    return HttpResponseRedirect("/main")


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
