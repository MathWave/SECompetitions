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
    return request.user.is_authenticated


def check_admin(request):
    return check_login(request) and request.user.is_staff


def check_superuser(request):
    return check_admin(request) and request.user.is_superuser


def check_permission(username, competition_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Permissions WHERE username = ? AND competition_id = ?', (username, competition_id))
    out = cursor.fetchall()
    cursor.execute('SELECT * FROM auth_user WHERE username = ? AND is_superuser = 1', (username,))
    is_superuser = len(cursor.fetchall()) != 0
    close_db(connector)
    if len(out) == 0 and not is_superuser:
        return False
    return True


########################################################################################################################


def users_sorting_key(x):
    return ' '.join(x[0:3])


def delete_user(request):
    if not check_superuser(request):
        return HttpResponseRedirect('/main')
    username = request.GET['user']
    connector, cursor = open_db()
    cursor.execute('DELETE FROM Users WHERE email = ?', (username,))
    cursor.execute('DELETE FROM auth_user WHERE username = ?', (username,))
    cursor.execute('DELETE FROM Solutions WHERE username = ?', (username,))
    close_db(connector)
    return HttpResponseRedirect('/superuser/main')


def get_new_user_inputs():
    values = ['surname', 'name', 'middle_name', 'group_name', 'email']
    line = '<tr>'
    for val in values:
        line += '<td><input type="text" name="' + val + '"></td>'
    line += '<td></td><td><input type="submit" value="Создать">'
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
        for field in user:
            line += '<td>' + field + '</td>'
        line += '<td><input type="button" onclick=delete_user("' + user[4] + '") value=Удалить></td></tr>'
    return line


def user_select():
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Users')
    users = [u[4] for u in cursor.fetchall()]
    close_db(connector)
    line = '<select name="user" id="user">'
    for user in sorted(users):
        line += '<option value="' + user + '">' + user + '</option>'
    line += '</select>'
    return line


def role_select():
    return '<select name="role" id="role">' \
           '<option value="user">Пользователь</option>' \
           '<option value="admin">Админ</option>' \
           '<option value="superuser">Бог</option>' \
           '</select>'


def role_table():
    columns_ru = ['Пользователь',  'Роль', '']
    line = '<tr>'
    for c in columns_ru:
        line += '<td><b>' + c + '</b></td>'
    line += '<tr><td>' + user_select() + '</td><td>' + role_select() + \
            '</td><td><input type="submit" value="Назначить"></td></tr>'
    return line



def send_email(subject, to_addr, from_addr, body_text):
    import smtplib

    body = "\r\n".join((
        "From: %s" % from_addr,
        "To: %s" % to_addr,
        "Subject: %s" % subject,
        "",
        body_text
    ))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('secompetitionssender@gmail.com', 'HSEguestHSEpassw0rd')
    server.sendmail(from_addr, [to_addr], body)
    server.quit()


def generate_password():
    from random import choice
    letters = 'qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBNM'
    password = ''
    for i in range(20):
        password += choice(letters)
    return password


def superuser(request):
    if not check_superuser(request):
        return HttpResponseRedirect('/main')
    if request.method == 'POST':
        if 'role' in request.POST.keys():
            connector, cursor = open_db()
            cursor.execute('UPDATE Users SET role = ? WHERE email = ?;', (request.POST['role'], request.POST['user']))
            if request.POST['role'] == 'user':
                is_staff, is_superuser = 0, 0
            elif request.POST['role'] == 'admin':
                is_staff, is_superuser = 1, 0
            else:
                is_staff, is_superuser = 1, 1
            cursor.execute('UPDATE auth_user SET is_staff = ?, is_superuser = ? WHERE username = ?',
                           (is_staff, is_superuser, request.POST['user']))
            close_db(connector)
        else:
            password = generate_password()
            text = 'Login: ' + request.POST['email'] + '\r\n'
            text += 'Password: ' + password
            from threading import Thread
            Thread(target=(lambda: send_email('Welcome to SECompetitions!', request.POST['email'],
                                              'secompetitionssender@gmail.com', text))).start()
            connector, cursor = open_db()
            cursor.execute('INSERT INTO Users VALUES (?, ?, ?, ?, ?, ?)', (
                request.POST['surname'],
                request.POST['name'],
                request.POST['middle_name'],
                request.POST['group_name'],
                request.POST['email'],
                'Пользователь'
            ))
            close_db(connector)
            user = User.objects.create_user(username=request.POST['email'], password=password)
            user.save()
    return render(request, 'superuser.html', context={'table': user_table(), 'role_table': role_table()})


########################################################################################################################


# получить список соревнований
def admin_competitions_table(request):
    connector, cursor = open_db()
    if request.user.is_superuser:
        cursor.execute("SELECT * FROM Competitions")
    else:
        cursor.execute("SELECT * FROM Competitions INNER JOIN Permissions ON "
                       "Competitions.id = Permissions.competition_id WHERE username = ?;", (request.user.username,))
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
    cursor.execute('SELECT * FROM Solutions AS A INNER JOIN Tasks AS B ON A.Task_id = B.id '
                   'INNER JOIN Users AS C ON A.username = C.email WHERE competition_id = ?', (competition_id,))
    solution_list = cursor.fetchall()
    close_db(connector)
    table = '<tr><td><b>Id</b></td><td><b>Таск</b></td><td><b>Пользователь</b></td><td><b>Вердикт</b></td></tr>'
    for solution in reversed(solution_list):
        table += '<tr>\n'
        table += "<td><a href='http://127.0.0.1:8000/admin/solution?solution_id=" + str(solution[0]) + "'>" + \
                 str(solution[0]) + '</a></td>'
        table += '<td>' + str(solution[5]) + '</td>\n'
        table += '<td>' + ' '.join(solution[12:15]) + '</td>'
        table += '<td>' + str(solution[3]) + '</td>'
        table += '</tr>\n'
    return table


def permissions_table(competition_id):
    line = '<tr><td><input type="text" name="input"></td><td><input type="submit" value="Добавить"></td></tr>'
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Permissions INNER JOIN Users ON '
                   'Permissions.username = Users.email;')
    perms = cursor.fetchall()
    close_db(connector)
    for perm in perms:
        line += '<tr><td>' + ' '.join(perm[3:6]) + '</td><td>' + perm[6] + '</td></tr>'
    return line


########################################################################################################################


def admin_delete_task(request):
    if not check_superuser(request):
        return HttpResponseRedirect('/main')
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
    if not check_superuser(request):
        return HttpResponseRedirect('/main')
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
    if not check_admin(request):
        return HttpResponseRedirect('/main')
    task_id = request.GET['task_id']
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (task_id,))
    competition_id = cursor.fetchone()[2]
    if not check_permission(request.user.username, competition_id):
        return HttpResponseRedirect('/main')
    cursor.execute('UPDATE Tasks SET tests_uploaded = 0 WHERE id = ?', (task_id,))
    close_db(connector)
    from os import remove
    remove('../data/tests/' + task_id + '.dll')
    return HttpResponseRedirect('/admin/task?task_id=' + task_id)


def admin_show_file(request):
    if not check_admin(request):
        return HttpResponseRedirect('/main')
    solution_id = request.GET['solution_id']
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions WHERE id = ?', (solution_id,))
    info = cursor.fetchone()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (info[1],))
    task_info = cursor.fetchone()
    cursor.execute('SELECT * FROM Competitions WHERE id = ?', (task_info[2],))
    competition = cursor.fetchone()
    close_db(connector)
    if not check_permission(request.user.username, competition[0]):
        return HttpResponseRedirect('/main')
    rootdir = '../data/solutions/' + str(solution_id) + '/' + request.GET.get('file', '')
    from os.path import dirname
    folder = '/'.join(dirname(rootdir).split('/')[4:])
    try:
        file = open(rootdir, 'r').read()
    except:
        return HttpResponseRedirect('/admin/solution?solution_id=' + str(solution_id) + '&folder=' + folder)
    return render(request, 'show_file.html', context={'competition': competition[1],
                                                      'task': task_info[1],
                                                      'username': info[2],
                                                      'id': solution_id,
                                                      'filename': rootdir.split('/')[-1],
                                                      'verdict': info[3],
                                                      'text': file,
                                                      'file': folder + '/' + rootdir.split('/')[-1],
                                                      'folder': folder})


def admin_solution(request):
    if not check_admin(request):
        return HttpResponseRedirect('/main')
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
    competition = cursor.fetchone()
    close_db(connector)
    if not check_permission(request.user.username, competition[0]):
        return HttpResponseRedirect('/main')
    return render(request, 'solution.html', context={'competition': competition[1],
                                                     'task': task_info[1],
                                                     'username': info[2],
                                                     'id': info[0],
                                                     'verdict': info[3],
                                                     'files': files,
                                                     'folder': 'root/' + folder,
                                                     'competition_id': task_info[2]})


def admin_solutions(request):
    if not check_admin(request) or not check_permission(request.user.username, request.GET['competition_id']):
        return HttpResponseRedirect('/main')
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Competitions WHERE id = ?', (request.GET['competition_id'],))
    name = cursor.fetchone()[1]
    close_db(connector)
    return render(request, "solutions.html",
                  context={'competition_id': request.GET['competition_id'],
                           'solutions': solutions_table(request.GET['competition_id']),
                           'name': name})


def admin_new_competition(request):
    if not check_superuser(request):
        return HttpResponseRedirect('/main')
    if request.method == 'GET':
        return render(request, "new_competition.html", context={"form": forms.NewCompetitionForm()})
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
    if not check_admin(request):
        return HttpResponseRedirect('/main')
    competition_id = request.GET['competition_id']
    if not check_permission(request.user.username, competition_id):
        return HttpResponseRedirect('/main')
    if request.method == 'POST':
        line = request.POST['input']
        connector, cursor = open_db()
        if '@' in line:
            cursor.execute('SELECT * FROM Users WHERE email = ?', (line,))
        elif any(c.isdigit() for c in line):
            cursor.execute('SELECT * FROM Users WHERE group_name = ?', (line,))
        else:
            try:
                s, n, m = line.split(' ')
            except:
                s, n, m = '', '', ''
            cursor.execute('SELECT * FROM Users WHERE surname = ? AND name = ? AND middle_name = ?', (s, n, m))
        newusers = cursor.fetchall()
        for user in newusers:
            cursor.execute('INSERT INTO Permissions (username, competition_id) VALUES (?, ?)',
                           (user[4], competition_id))
        close_db(connector)
    connector, cursor = open_db()
    cursor.execute('SELECT competition_name FROM Competitions WHERE id = ?', (competition_id,))
    name = cursor.fetchone()[0]
    return render(request, "competitions_settings.html",
                  context={"name": name,
                           'tasks': admin_tasks_table(request.GET['competition_id']),
                           'competition_id': request.GET['competition_id'],
                           'is_superuser': request.user.is_superuser,
                           'permissions_table': permissions_table(request.GET['competition_id'])})


def admin_task(request):
    if not check_admin(request):
        return HttpResponseRedirect('/main')
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (request.GET['task_id'],))
    this_task = cursor.fetchone()
    cursor.execute('SELECT competition_name from Competitions WHERE id = ?', (this_task[2],))
    competition_name = cursor.fetchone()[0]
    if not check_permission(request.user.username, this_task[2]):
        return HttpResponseRedirect('/main')
    context = {'competition': competition_name, 'task': this_task[1], 'legend': this_task[3], 'input': this_task[4],
               'output': this_task[5], 'specifications': this_task[6], 'tests_uploaded': bool(this_task[7]),
               'tests': forms.TestsForm(), 'competition_id': this_task[2], 'task_id': request.GET['task_id'],
               'is_superuser': request.user.is_superuser}
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
    return render(request, 'task_settings.html', context=context)


def admin_new_task(request):
    if not check_superuser(request):
        return HttpResponseRedirect('/main')
    connector, cursor = open_db()
    cursor.execute('SELECT competition_name FROM Competitions WHERE id = ?', (request.GET['competition_id'],))
    competition_name = cursor.fetchone()[0]
    if request.method == 'GET':
        return render(request, 'new_task.html', context={'form': forms.NewTaskForm(),
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
    if not check_admin(request):
        return HttpResponseRedirect('/main')
    return render(request, "admin.html", context={"competitions": admin_competitions_table(request),
                                                  'is_superuser': request.user.is_superuser})


########################################################################################################################


# получить список всех соревнований (потом надо будет сделать фильтр)
def competitions_table(request):
    connector, cursor = open_db()
    if request.user.is_superuser:
        cursor.execute("SELECT * FROM Competitions")
    else:
        cursor.execute("SELECT * FROM Competitions INNER JOIN Permissions ON "
                       "Competitions.id = Permissions.competition_id WHERE username = ?;", (request.user.username,))
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
    if not check_login(request):
        return HttpResponseRedirect('/enter')
    return render(request, "main.html", context={"competitions": competitions_table(request),
                                                 'is_admin': request.user.is_staff})


def redirect(request):
    return HttpResponseRedirect('/main')


def competition(request):
    if not check_login(request) or not check_permission(request.user.username, request.GET['competition_id']):
        return HttpResponseRedirect('/enter')
    connector, cursor = open_db()
    cursor.execute('SELECT competition_name FROM Competitions WHERE id = ?', (request.GET['competition_id'],))
    name = cursor.fetchone()[0]
    return render(request, "competition.html", context={"name": name,
                                                        'tasks': tasks_table(request.GET['competition_id']),
                                                        'is_admin': request.user.is_staff})


def task(request):
    if not check_login(request):
        return HttpResponseRedirect('/enter')
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (request.GET['task_id'],))
    this_task = cursor.fetchone()
    cursor.execute('SELECT competition_name FROM Competitions WHERE id = ?', (this_task[2],))
    competition_name = cursor.fetchone()[0]
    close_db(connector)
    check_permission(request.user.username, this_task[2])
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
            'competition_id': this_task[2],
            'is_admin': request.user.is_staff
        }
        return render(request, "task.html", context=context)
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
    return render(request, 'settings.html', context={'is_admin': request.user.is_staff})


def restore(request):
    if not check_login(request):
        return HttpResponseRedirect('/enter')
    return HttpResponseRedirect("/main")


def enter(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/main")
    if request.method == "POST":
        user = authenticate(username=request.POST.get('email'), password=request.POST.get('password'))
        if user is not None:
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
