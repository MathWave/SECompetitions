from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from contest import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from sqlite3 import connect
from zipfile import ZipFile as zf
from urllib.request import quote
from contest.methods import open_db, close_db


########################################################################################################################


def check_login(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/enter')


def check_admin(request):
    check_login(request)
    if not request.user.is_staff:
        return HttpResponseRedirect('/enter')


def check_superuser(request):
    check_admin(request)
    if not request.user.is_superuser:
        return HttpResponseRedirect('/enter')


def has_permission(username, competition_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Permissons WHERE username = ? AND competition_id = ?', (username, competition_id))
    out = cursor.fetchall()
    cursor.execute('SELECT * FROM user_auth WHERE username = ? AND is_superuser = 1', (username,))
    is_superuser = len(cursor.fetchall()) != 0
    close_db(connector)
    return len(out) != 0 or is_superuser


########################################################################################################################


def users_sorting_key(x):
    return ' '.join(x[0:3])


def get_select(selected):
    return '<select id="role" selected="' + selected + '">' \
                                                       '<option value="user">Пользователь</option>' \
                                                       '<option value="admin">Админ</option>' \
                                                       '<option value="superuser">Бог</option></select>'


def get_new_user_inputs():
    values = ['surname', 'name', 'middle_name', 'droup_name', 'email']
    line = '<tr>'
    for val in values:
        line += '<td><input type="text" name="' + val + '"></td>'
    line += '<td>' + get_select('user') + '</td><td><input type="submit" value="Создать">'
    return line


def user_table():
    columns_ru = ['Фамилия', 'Имя', 'Отчество', 'Группа', 'Почта', 'Роль']
    line = '<tr>'
    for c in columns_ru:
        line += '<td><b>' + c + '</b></td>'
    line += '<td></td></tr><tr>' + get_new_user_inputs() + '</tr>'
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Users')
    users = cursor.fetchall()
    close_db(connector)
    for user in sorted(users, key=users_sorting_key):
        line += '<tr>'
        for i in range(0, 5):
            line += '<td>' + user[i] + '</td>'
        line += '<td>' + get_select(user[5]) + '</td>'
        line += '</tr>'
    return line


def superuser(request):
    check_superuser(request)
    if request.method == 'GET':
        return render(request, 'superuser/superuser.html', context={'table': user_table()})
    else:
        return HttpResponseRedirect('/main')


########################################################################################################################


# получить список соревнований
def admin_competitions_table():
    connector, cursor = open_db()
    cursor.execute("SELECT * FROM Competitions")
    comps = cursor.fetchall()
    line = '<table>\n'
    for c in comps:
        line += '<tr><td><a href="http://127.0.0.1:8000/admin/competition?competition_id=' + str(c[0]) + '">' + c[
            1] + '</td></tr>\n'
    line += '</table>'
    close_db(connector)
    return line


def admin_tasks_table(competition_id):
    connector, cursor = open_db()
    cursor.execute("SELECT * FROM Tasks WHERE competition_id = ?", (competition_id,))
    tasks = cursor.fetchall()
    close_db(connector)
    line = '<table>\n'
    for c in tasks:
        line += '<tr><td><a href="http://127.0.0.1:8000/admin/task?task_id=' + str(c[0]) + '">' + c[1] + '</td></tr>\n'
    line += '</table>'
    return line


def solutions_table(competition_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions '
                   'INNER JOIN Tasks ON Solutions.Task_id = Tasks.id '
                   'WHERE competition_id = ?', (competition_id,))
    solution_list = cursor.fetchall()
    close_db(connector)
    table = '<tr><td><b>Id</b></td><td><b>Таск</b></td><td><b>Пользователь</b></td><td><b>Вердикт</b></td></tr>'
    for solution in reversed(solution_list):
        table += '<tr>\n'
        table += "<td><a href='http://127.0.0.1:8000/admin/solution?solution_id=" + str(solution[0]) + "'>" + \
                 str(solution[0]) + '</a></td>'
        for i in 5, 2, 3:
            table += '<td>' + str(solution[i]) + '</td>\n'
        table += '</tr>\n'
    return table


########################################################################################################################


def admin_delete_task(request):
    check_admin(request)
    task_id = request.GET['task_id']
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('SELECT competition_id FROM Tasks WHERE id = ?', (task_id,))
    competition_id = cursor.fetchone()[0]
    cursor.execute('SELECT * FROM Solutions WHERE task_id = ?', (task_id,))
    solutions_ids = [s[0] for s in cursor.fetchall()]
    cursor.execute('DELETE FROM Solutions WHERE task_id = ?', (task_id,))
    cursor.execute('DELETE FROM Tasks WHERE id = ?', (task_id,))
    close_db(connector)
    from shutil import rmtree
    from os import remove
    for i in solutions_ids:
        rmtree('../data/solutions/' + str(i))
    remove('../data/tests/' + str(task_id) + '.dll')
    return HttpResponseRedirect('/admin/competition?competition_id=' + str(competition_id))


def admin_delete_competition(request):
    check_admin(request)
    competition_id = request.GET['competition_id']
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE competition_id = ?', (competition_id,))
    task_ids = [(i[0],) for i in cursor.fetchall()]
    from os import remove
    from shutil import rmtree
    for i in task_ids:
        cursor.execute('SELECT * FROM Solutions WHERE task_id = ?;', i)
        for s in cursor.fetchall():
            rmtree('../data/solutions/' + str(s[0]))
        remove('../data/tests/' + str(i[0]) + '.dll')
    cursor.executemany('DELETE FROM Solutions WHERE task_id = ?', task_ids)
    cursor.execute('DELETE FROM Tasks WHERE competition_id = ?', (competition_id,))
    cursor.execute('DELETE FROM Competitions WHERE id = ?', (competition_id,))
    cursor.execute('DELETE FROM Permissions WHERE competition_id = ?', (competition_id,))
    close_db(connector)
    return HttpResponseRedirect('/admin/main')


def admin_remove_tests(request):
    check_admin(request)
    task_id = request.GET['task_id']
    connector, cursor = open_db()
    cursor.execute('UPDATE Tasks SET tests_uploaded = 0 WHERE id = ?', (task_id,))
    close_db(connector)
    from os import remove
    remove('../data/tests/' + task_id + '.dll')
    return HttpResponseRedirect('/admin/task?task_id=' + task_id)


def admin_show_file(request):
    check_admin(request)
    solution_id = request.GET['solution_id']
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions WHERE id = ?', (solution_id,))
    info = cursor.fetchone()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (info[1],))
    task_info = cursor.fetchone()
    cursor.execute('SELECT * FROM Competitions WHERE id = ?', (task_info[2],))
    competition = cursor.fetchone()[1]
    close_db(connector)
    rootdir = '../data/solutions/' + str(solution_id) + '/' + request.GET.get('file', '')
    from os.path import dirname
    folder = '/'.join(dirname(rootdir).split('/')[4:])
    try:
        file = open(rootdir, 'r').read()
    except:
        return HttpResponseRedirect('/admin/solution?solution_id=' + str(solution_id) + '&folder=' + folder)
    return render(request, 'admin/show_file.html', context={'competition': competition,
                                                            'task': task_info[1],
                                                            'username': info[2],
                                                            'id': solution_id,
                                                            'filename': rootdir.split('/')[-1],
                                                            'verdict': info[3],
                                                            'text': file,
                                                            'file': folder + '/' + rootdir.split('/')[-1],
                                                            'folder': folder
                                                            })


def admin_solution(request):
    check_admin(request)
    solution_id = request.GET['solution_id']
    folder = request.GET.get('folder', '')
    if '..' in folder:
        return HttpResponseRedirect('/enter')
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions WHERE id = ?', (solution_id,))
    info = cursor.fetchone()
    files = ''
    if folder:
        files += '<div><img src="http://icons.iconarchive.com/icons/icons8/ios7/16/Very-Basic-Opened-Folder-icon.png'
        split_folder = folder.split('/')
        files += '">    <a href=http://127.0.0.1:8000/admin/solution?solution_id=' + str(solution_id) + '&folder=' + \
                 quote('/'.join(split_folder[0:len(split_folder) - 1]), safe='') + '>..</div>\n'
    from os import listdir
    from os.path import isfile, join
    rootdir = '../data/solutions/' + str(solution_id) + '/' + folder
    for file in sorted(listdir(rootdir)):
        current_file = join(rootdir, file)
        files += '<div><img src="'
        if isfile(current_file):
            files += 'http://icons.iconarchive.com/icons/icons8/windows-8/16/Very-Basic-Document-icon.png'
            f = '/'.join(rootdir.split('/')[6:])
            files += '">    <a href=http://127.0.0.1:8000/admin/show_file?solution_id=' + str(solution_id) + '&file=' + \
                     quote('/'.join(current_file.split('/')[4:]), safe='') + '>' + file + '</div>\n'
        else:
            files += 'http://icons.iconarchive.com/icons/icons8/ios7/16/Very-Basic-Opened-Folder-icon.png'
            files += '">    <a href=http://127.0.0.1:8000/admin/solution?solution_id=' + str(solution_id) + '&folder=' + \
                     quote('/'.join(current_file.split('/')[4:]), safe='') + '>' + file + '</div>\n'
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (info[1],))
    task_info = cursor.fetchone()
    cursor.execute('SELECT * FROM Competitions WHERE id = ?', (task_info[2],))
    competition = cursor.fetchone()[1]
    close_db(connector)
    return render(request, 'admin/solution.html', context={'competition': competition,
                                                           'task': task_info[1],
                                                           'username': info[2],
                                                           'id': info[0],
                                                           'verdict': info[3],
                                                           'files': files,
                                                           'folder': 'root/' + folder,
                                                           'competition_id': task_info[2]
                                                           })


def admin_solutions(request):
    check_admin(request)
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Competitions WHERE id = ?', (request.GET['competition_id']))
    name = cursor.fetchone()[1]
    close_db(connector)
    return render(request, "admin/solutions.html",
                  context={'competition_id': request.GET['competition_id'],
                           'solutions': solutions_table(request.GET['competition_id']),
                           'name': name})


def admin_new_competition(request):
    check_admin(request)
    if request.method == 'GET':
        return render(request, "admin/new_competition.html", context={"form": forms.NewCompetitionForm()})
    else:
        name = request.POST['name']
        connector, cursor = open_db()
        cursor.execute("INSERT INTO Competitions (competition_name) VALUES (?);", (name,))
        close_db(connector)
        connector, cursor = open_db()
        cursor.execute('SELECT id FROM Competitions WHERE competition_name = ?', (request.POST['name'],))
        competition_id = cursor.fetchone()[0]
        close_db(connector)
        return HttpResponseRedirect('/admin/competition?competition_id=' + str(competition_id))


def admin_competition(request):
    check_admin(request)
    competition_id = request.GET['competition_id']
    connector, cursor = open_db()
    cursor.execute('SELECT competition_name FROM Competitions WHERE id = ?', (competition_id,))
    name = cursor.fetchone()[0]
    return render(request, "admin/competitions_settings.html",
                  context={"name": name,
                           'tasks': admin_tasks_table(request.GET['competition_id']),
                           'competition_id': request.GET['competition_id']})


def admin_task(request):
    check_admin(request)
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (request.GET['task_id'],))
    this_task = cursor.fetchone()
    cursor.execute('SELECT competition_name from Competitions WHERE id = ?', (this_task[2],))
    competition_name = cursor.fetchone()[0]
    context = {'competition': competition_name, 'task': this_task[1], 'legend': this_task[3], 'input': this_task[4],
               'output': this_task[5], 'specifications': this_task[6], 'tests_uploaded': bool(this_task[7]),
               'tests': forms.TestsForm(), 'competition_id': this_task[2], 'task_id': request.GET['task_id']}
    if request.method == 'POST':
        have_tests = int('tests' in request.FILES.keys())
        cursor.execute("UPDATE Tasks SET "
                       "legend = ?, "
                       "input = ?, "
                       "output = ?, "
                       "specifications = ?, "
                       "tests_uploaded = ? "
                       "WHERE id = ?;",
                       (request.POST['legend'],
                        request.POST['input'],
                        request.POST['output'],
                        request.POST['specifications'],
                        have_tests,
                        request.GET['task_id']))
        from os import system
        if have_tests:
            file = request.FILES['tests']
            cursor.execute('UPDATE Tasks SET tests_uploaded = 1 WHERE id = ?', (request.GET['task_id'],))
            context['tests_uploaded'] = True
            test_file = '../data/tests/' + str(this_task[0]) + '.dll'
            system('touch ' + test_file)
            with open(test_file, 'wb+') as fs:
                for chunk in file.chunks():
                    fs.write(chunk)
        close_db(connector)
    return render(request, 'admin/task_settings.html', context=context)


def admin_new_task(request):
    check_admin(request)
    connector, cursor = open_db()
    cursor.execute('SELECT competition_name FROM Competitions WHERE id = ?', (request.GET['competition_id'],))
    competition_name = cursor.fetchone()[0]
    if request.method == 'GET':
        return render(request, 'admin/new_task.html', context={'form': forms.NewTaskForm(),
                                                               'name': competition_name,
                                                               'competition_id': request.GET['competition_id']})
    else:
        task_name = request.POST['name']
        cursor.execute('SELECT * FROM Tasks')
        full = cursor.fetchall()
        index = full[-1][0] + 1 if full else 1
        cursor.execute("INSERT INTO Tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (index,
                                                                             task_name,
                                                                             request.GET['competition_id'],
                                                                             '',
                                                                             '',
                                                                             '',
                                                                             '',
                                                                             0))
        close_db(connector)
        return HttpResponseRedirect('/admin/task?task_id=' + str(index))


def admin_main(request):
    check_admin(request)
    return render(request, "admin/admin.html", context={"competitions": admin_competitions_table(),
                                                        'is_superuser': request.user.is_superuser})


########################################################################################################################


# получить список всех соревнований (потом надо будет сделать фильтр)
def competitions_table():
    connector, cursor = open_db()
    cursor.execute("SELECT * FROM Competitions")
    comps = cursor.fetchall()
    line = '<table>\n'
    for c in comps:
        line += '<tr><td><a href="http://127.0.0.1:8000/competition?competition_id=' + str(c[0]) + '">' + c[
            1] + '</td></tr>\n'
    line += '</table>'
    close_db(connector)
    return line


# получить таблицу с заданиями из соревнования competition_name
def tasks_table(competition_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE competition_id = ?', (competition_id,))
    tasks = cursor.fetchall()
    line = '<table>\n'
    for c in tasks:
        line += '<tr><td><a href="http://127.0.0.1:8000/task?task_id=' + str(c[0]) + '">' + c[1] + \
                '</td></tr>\n'
    line += '</table>'
    return line


def task_solutions_table(task_id, username):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions WHERE task_id = ? AND username = ?', (task_id, username))
    solution_list = cursor.fetchall()
    close_db(connector)
    table = '<tr><td><b>Id</b></td><td><b>Вердикт</b></td></tr>'
    for solution in reversed(solution_list):
        table += '<tr>\n'
        for i in 0, 3:
            table += '<td>' + str(solution[i]) + '</td>\n'
        table += '</tr>\n'
    return table


########################################################################################################################


def main(request):
    check_login(request)
    if request.user.is_staff:
        return render(request, "admin/main.html", context={"competitions": competitions_table()})
    else:
        return render(request, "competitor/main.html", context={"competitions": competitions_table()})


def redirect(request):
    return HttpResponseRedirect('/main')


def competition(request):
    check_login(request)
    connector, cursor = open_db()
    cursor.execute('SELECT competition_name FROM Competitions WHERE id = ?', (request.GET['competition_id'],))
    name = cursor.fetchone()[0]
    if request.user.is_staff:
        return render(request, "admin/competition.html", context={"name": name,
                                                                  'tasks': tasks_table(request.GET['competition_id'])})
    else:
        return render(request, "competitor/competition.html", context={"name": name,
                                                                       'tasks': tasks_table(
                                                                           request.GET['competition_id'])})


def task(request):
    check_login(request)
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (request.GET['task_id'],))
    this_task = cursor.fetchone()
    cursor.execute('SELECT competition_name FROM Competitions WHERE id = ?', (this_task[2],))
    competition_name = cursor.fetchone()[0]
    close_db(connector)
    if request.method == 'GET':
        context = {
            'competition_name': competition_name,
            'task_name': this_task[1],
            'legend': this_task[3].replace('\n', '<br>'),
            'input': this_task[4].replace('\n', '<br>'),
            'output': this_task[5].replace('\n', '<br>'),
            'specifications': this_task[6].replace('\n', '<br>'),
            'form': forms.FileForm(),
            'solutions': task_solutions_table(this_task[0], request.user.username),
            'competition_id': this_task[2]
        }
        if request.user.is_staff:
            return render(request, "admin/task.html", context=context)
        else:
            return render(request, "competitor/task.html", context=context)
    else:
        if 'file' in request.FILES.keys():
            file = request.FILES['file']
            this_directory = '../data/solutions/'
            connector, cursor = open_db()
            cursor.execute('SELECT * FROM Solutions')
            all = cursor.fetchall()
            index = all[-1][0] + 1 if all else 1
            cursor.execute("INSERT INTO Solutions VALUES (?, ?, ?, 'TESTING')",
                           (index, this_task[0], request.user.username))
            close_db(connector)
            solution_dir = this_directory + str(index) + '/'
            from os import mkdir
            mkdir(solution_dir)
            with open(solution_dir + 'solution.zip', 'wb') as fs:
                for chunk in file.chunks():
                    fs.write(chunk)
            from os import remove, listdir
            with zf(solution_dir + 'solution.zip') as obj:
                obj.extractall(solution_dir)
            remove(solution_dir + 'solution.zip')
            from contest.TesterGlobal import TesterGlobal
            TesterGlobal(index, this_task[0], this_task[1], request.user.username, 10000).start()
        return HttpResponseRedirect('/task?task_id=' + str(this_task[0]))


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


def reset(request):
    connector, cursor = open_db()
    cursor.execute('DROP TABLE IF EXISTS Solutions;')
    cursor.execute('DROP TABLE IF EXISTS Competitions;')
    cursor.execute('DROP TABLE IF EXISTS Tasks;')
    cursor.execute('DROP TABLE IF EXISTS Users;')
    cursor.execute('DROP TABLE IF EXISTS Permissions;')
    cursor.execute(
        '''
        CREATE TABLE Solutions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            username TEXT,
            result TEXT
        );
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE Competitions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_name TEXT
        );
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE Tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            competition_id INTEGER,
            legend TEXT,
            input TEXT,
            output TEXT,
            specifications TEXT,
            tests_uploaded INTEGER
        );
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE Users(
            surname TEXT,
            name TEXT,
            middle_name TEXT,
            group_name TEXT,
            email TEXT,
            role TEXT
        );
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE Permissions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            competition_id INTEGER
        );
        '''
    )
    close_db(connector)
    from os import system
    from os.path import exists
    if exists('../data'):
        system('rm -r ../data')
    system('mkdir ../data')
    system('mkdir ../data/solutions')
    system('mkdir ../data/tests')
    return HttpResponseRedirect('/main')

# ======================================================================================================================

# ======================================================================================================================
