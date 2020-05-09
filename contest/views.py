from django.shortcuts import render
from django.http import HttpResponseRedirect
from contest import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from zipfile import ZipFile as zf
from contest.extra_funcs import *
from contest.html_generators import *


def download(request):
    sols = solutions_by_request(request.GET)
    if len(sols) == 0:
        return HttpResponseRedirect('/admin/solutions?block_id=' + request.GET['block_id'])
    from os import listdir
    from os import mkdir
    cur_folder = 1
    while str(cur_folder) in listdir('../data/collecting_dir'):
        cur_folder += 1
    mkdir('../data/collecting_dir/' + str(cur_folder))
    cur_folder = '../data/collecting_dir/' + str(cur_folder) + '/solutions'
    mkdir(cur_folder)
    for sol in sols:
        solution_id = sol['solution_id']
        shell('cp -r ../data/solutions/' + str(solution_id) + ' ' + cur_folder)
    from os.path import dirname, join
    zip_folder = join(dirname(cur_folder), 'solutions.zip')
    shell('python3 -m zipfile -c ' + zip_folder + ' ' + cur_folder + '/')
    f = open(zip_folder, 'rb').read()
    from shutil import rmtree
    rmtree(dirname(cur_folder))
    from django.http import HttpResponse
    response = HttpResponse(f, content_type='application/force-download')
    connector, cursor = open_db()
    cursor.execute('SELECT block_name FROM Blocks WHERE id = ?', (request.GET['block_id'],))
    name = cursor.fetchone()[0]
    response['Content-Disposition'] = 'inline; filename=' + name + '.zip'
    return response



def unsubscribe(request):
    username = request.GET['username']
    course_id = request.GET['course_id']
    if not check_teacher(request) or not check_permission_course(request.user.username, course_id):
        return HttpResponseRedirect('/main')
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions AS A '
                   'INNER JOIN Tasks AS B ON A.task_id = B.id '
                   'INNER JOIN Blocks AS C ON B.block_id = C.id '
                   'WHERE A.username = ? AND C.course_id = ?', (username, course_id))
    cursor.execute('DELETE FROM Subscribes WHERE username = ? AND course_id = ?', (username, course_id))
    cursor.execute('SELECT id FROM Blocks WHERE course_id = ?', (course_id,))
    ids = [i[0] for i in cursor.fetchall()]
    for i in ids:
        cursor.execute('DELETE FROM Marks WHERE username = ? AND block_id = ?', (username, i))
    close_db(connector)
    return HttpResponseRedirect('/admin/users_settings?course_id=' + str(course_id))


def users_settings(request):
    course_id = request.GET['course_id']
    if not check_teacher(request) or not check_permission_course(request.user.username, course_id):
        return HttpResponseRedirect('/main')
    if request.method == 'POST':
        connector, cursor = open_db()
        if 'input' in request.POST.keys():
            line = request.POST['input']
            if '@' in line:
                cursor.execute('SELECT email FROM Users WHERE email = ?', (line,))
            elif any(c.isdigit() for c in line):
                cursor.execute('SELECT email FROM Users WHERE group_name = ?', (line,))
            else:
                try:
                    s, n, m = line.split(' ')
                except:
                    s, n, m = '', '', ''
                cursor.execute('SELECT email FROM Users WHERE surname = ? AND name = ? AND middle_name = ?', (s, n, m))
            newusers = [u[0] for u in cursor.fetchall()]
            us = [u[4] for u in users_in_course(course_id)]
            for user in newusers:
                if user not in us:
                    cursor.execute('INSERT INTO Subscribes VALUES (?, ?, 0)',
                                   (user, course_id))
        else:
            username = request.POST['user']
            cursor.execute('SELECT is_assistant FROM Subscribes WHERE course_id = ? AND username = ?', (course_id, username))
            res = 1 - cursor.fetchone()[0]
            cursor.execute('UPDATE Subscribes SET is_assistant = ? WHERE course_id = ? AND username = ?', (res, course_id, username))
        close_db(connector)
    connector, cursor = open_db()
    cursor.execute("SELECT * FROM Courses WHERE id = ?", (course_id,))
    course = cursor.fetchone()
    close_db(connector)
    return render(request, 'users_settings.html', context={'table': user_table(course_id), 'name': course[1], 'users': users_select(course_id)})


def delete_user(request):
    if not check_teacher(request):
        return HttpResponseRedirect('/main')
    username = request.GET['user']
    connector, cursor = open_db()
    cursor.execute('DELETE FROM Users WHERE email = ?', (username,))
    cursor.execute('DELETE FROM auth_user WHERE username = ?', (username,))
    cursor.execute('DELETE FROM Solutions WHERE username = ?', (username,))
    cursor.execute('DELETE FROM Subscribes WHERE username = ?', (username,))
    cursor.execute('DELETE FROM Marks WHERE username = ?', (username,))
    close_db(connector)
    return HttpResponseRedirect('/superuser/main')


def superuser(request):
    if not check_god(request):
        return HttpResponseRedirect('/main')
    if request.method == 'POST':
        if 'role' in request.POST.keys():
            connector, cursor = open_db()
            if request.POST['role'] == 'user':
                role_id = 0
            else:
                role_id = 1
            cursor.execute('UPDATE auth_user SET is_staff = ? WHERE username = ?', (role_id, request.POST['user']))
            close_db(connector)
        elif 'request' in request.POST.keys():
            req = request.POST['request']
            connector, cursor = open_db()
            cursor.execute(req)
            close_db(connector)
        else:
            connector, cursor = open_db()
            cursor.execute('SELECT * FROM Courses;')
            courses = cursor.fetchall()
            index = 1 if not courses else courses[-1][0] + 1
            cursor.execute('INSERT INTO Courses VALUES (?, ?);', (index, request.POST['course_name']))
            cursor.execute('INSERT INTO Subscribes VALUES (?, ?, 0)', (request.POST['teacher'], index))
            close_db(connector)
    return render(request, 'superuser.html', context={'table': user_table(), 'role_table': role_table(), 'top': courses_table_create(), 'courses_table': courses_table()})


def delete_task(request):
    if not check_teacher(request):
        return HttpResponseRedirect('/main')
    task_id = request.GET['task_id']
    connector, cursor = open_db()
    cursor.execute('SELECT block_id FROM Tasks WHERE id = ?', (task_id,))
    block_id = cursor.fetchone()[0]
    close_db(connector)
    if not check_permission_admin(request.user.username, block_id):
        return HttpResponseRedirect('/main')
    delete_task_extra(task_id)
    return HttpResponseRedirect('/admin/block?block_id=' + str(block_id))


def delete_block(request):
    if not check_teacher(request):
        return HttpResponseRedirect('/main')
    block_id = request.GET['block_id']
    if not check_permission_admin(request.user.username, block_id):
        return HttpResponseRedirect('/main')
    delete_block_extra(block_id)
    return HttpResponseRedirect('/admin/main')


def remove_tests(request):
    if not check_assistant(request):
        return HttpResponseRedirect('/main')
    task_id = request.GET['task_id']
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (task_id,))
    block_id = cursor.fetchone()[2]
    close_db(connector)
    if not check_permission_admin(request.user.username, block_id):
        return HttpResponseRedirect('/main')
    from os import remove
    remove('../data/tests/' + task_id + '.dll')
    return HttpResponseRedirect('/admin/task?task_id=' + task_id)


def show_file(request):
    if not check_assistant(request):
        return HttpResponseRedirect('/main')
    solution_id = request.GET['solution_id']
    if request.method == 'POST':
        set_mark(solution_id, request.POST['mark'])
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions WHERE id = ?', (solution_id,))
    info = cursor.fetchone()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (info[1],))
    task_info = cursor.fetchone()
    cursor.execute('SELECT * FROM Blocks WHERE id = ?', (task_info[2],))
    comp = cursor.fetchone()
    cursor.execute('SELECT * FROM Users WHERE email = ?', (info[2],))
    username = ' '.join(cursor.fetchone()[0:3])
    close_db(connector)
    c = {x: request.GET[x] for x in request.GET.keys()}
    c.pop('file')
    c.pop('solution_id')
    if not check_permission_admin(request.user.username, comp[0]):
        return HttpResponseRedirect('/main')
    rootdir = '../data/solutions/' + str(solution_id) + '/' + request.GET.get('file', '')
    from os.path import dirname
    folder = '/'.join(dirname(rootdir).split('/')[4:])
    try:
        file = open(rootdir, 'r').read()
    except:
        return HttpResponseRedirect('/admin/solution?solution_id=' + str(solution_id) + '&folder=' + folder)
    return render(request, 'show_file.html', context={'info_table': solution_info_table(solution_id),
                                                      'text': file,
                                                      'id': solution_id,
                                                      'file': folder + '/' + rootdir.split('/')[-1],
                                                      'folder': folder,
                                                      'req': get_req(c)})


def solution(request):
    if not check_assistant(request):
        return HttpResponseRedirect('/main')
    solution_id = request.GET['solution_id']
    folder = request.GET.get('folder', '')
    if request.method == 'POST':
        set_mark(solution_id, request.POST['mark'])
    if '..' in folder:
        return HttpResponseRedirect('/enter')
    from urllib.request import quote
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions WHERE id = ?', (solution_id,))
    info = cursor.fetchone()
    files = ''
    c = {x: request.GET[x] for x in request.GET.keys()}
    c.pop('solution_id')
    if 'folder' in c.keys():
        c.pop('folder')
    if folder:
        files += '<div><img src="http://icons.iconarchive.com/icons/icons8/ios7/16/Very-Basic-Opened-Folder-icon.png'
        split_folder = folder.split('/')
        files += '">    <a href=http://mathwave.pythonanywhere.com/admin/solution?solution_id=' + str(solution_id) + '&folder=' + \
                 quote('/'.join(split_folder[0:len(split_folder) - 1]), safe='') + get_req(c) + '>..</div>\n'
    from os import listdir
    from os.path import isfile, join
    rootdir = '../data/solutions/' + str(solution_id) + '/' + folder
    for file in sorted(listdir(rootdir.replace('//', '/'))):
        current_file = join(rootdir, file)
        files += '<div><img src="'
        if isfile(current_file):
            files += 'http://icons.iconarchive.com/icons/icons8/windows-8/16/Very-Basic-Document-icon.png'
            f = '/'.join(rootdir.split('/')[6:])
            files += '">    <a href=http://mathwave.pythonanywhere.com/admin/show_file?solution_id=' + str(solution_id) + '&file=' + \
                     quote('/'.join(current_file.split('/')[4:]), safe='') + get_req(c) + '>' + file + '</div>\n'
        else:
            files += 'http://icons.iconarchive.com/icons/icons8/ios7/16/Very-Basic-Opened-Folder-icon.png'
            files += '">    <a href=http://mathwave.pythonanywhere.com/admin/solution?solution_id=' + str(solution_id) + '&folder=' + \
                     quote('/'.join(current_file.split('/')[4:]), safe='') + get_req(c) + '>' + file + '</div>\n'
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (info[1],))
    task_info = cursor.fetchone()
    cursor.execute('SELECT * FROM Blocks WHERE id = ?', (task_info[2],))
    block = cursor.fetchone()
    cursor.execute('SELECT * FROM Users WHERE email = ?', (info[2],))
    username = ' '.join(cursor.fetchone()[0:3])
    close_db(connector)
    if not check_permission_admin(request.user.username, block[0]):
        return HttpResponseRedirect('/main')
    sols = solutions_by_request(request.GET)
    left, right = '', ''
    cur = 0
    for s in range(len(sols)):
        if sols[s]['solution_id'] == int(solution_id):
            cur = s
            break
    req = get_req(c)
    if 'block_id' in c.keys():
        c.pop('block_id')
    back_req = get_req(c)
    if len(sols) == 1:
        pass
    else:
        if cur != 0:
            left = '<a href="http://mathwave.pythonanywhere.com/admin/solution?solution_id=' + str(sols[cur - 1]['solution_id']) + req + '"><-</a>'
        if cur != len(sols) - 1:
            right = '<a href="http://mathwave.pythonanywhere.com/admin/solution?solution_id=' + str(sols[cur + 1]['solution_id']) + req + '">-></a>'
    return render(request, 'solution.html', context={'info_table': solution_info_table(solution_id),
                                                     'block_id': task_info[2],
                                                     'req': back_req,
                                                     'files': files,
                                                     'folder': 'root/' + folder,
                                                     'files_text': solution_files_text(solution_id),
                                                     'previous': left,
                                                     'next': right})


def solutions(request):
    if not check_permission_admin(request.user.username, request.GET['block_id']):
        return HttpResponseRedirect('/main')
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Blocks WHERE id = ?', (request.GET['block_id'],))
    name = cursor.fetchone()[1]
    close_db(connector)
    req = '&'.join([str(key) + '=' + str(request.GET[key]) for key in request.GET.keys()])
    return render(request, "solutions.html",
                  context={'block_id': request.GET['block_id'],
                           'solutions': solutions_table(request.GET),
                           'name': name,
                           'req': req})


def new_block(request):
    if not check_teacher(request):
        return HttpResponseRedirect('/main')
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Subscribes WHERE course_id = ? AND username = ?', (request.GET['course_id'], request.user.username))
    l = cursor.fetchall()
    close_db(connector)
    if not l:
        return HttpResponseRedirect('/main')
    if request.method == 'GET':
        connector, cursor = open_db()
        cursor.execute('SELECT * FROM Courses WHERE id = ?', (request.GET['course_id'],))
        name = cursor.fetchone()[1]
        close_db(connector)
        return render(request, "new_block.html", context={"form": forms.NewCompetitionForm(), 'name': name})
    else:
        name = request.POST['name']
        course_id = request.GET['course_id']
        connector, cursor = open_db()
        cursor.execute('SELECT * FROM Blocks;')
        a = cursor.fetchall()
        index = a[-1][0] + 1 if a else 1
        cursor.execute("INSERT INTO Blocks VALUES (?, ?, ?, ?, ?, ?);", (index, name, course_id, "0000-00-00 00:00:00", "0000-00-00 00:00:00", 0))
        cursor.execute('SELECT username FROM Subscribes WHERE course_id = ?', (course_id,))
        users = [u[0] for u in cursor.fetchall()]
        for u in users:
            cursor.execute('INSERT INTO Marks VALUES(?, ?, 0);', (u, index))
        close_db(connector)
        return HttpResponseRedirect('/admin/block?block_id=' + str(index))


def block_settings(request):
    if not check_assistant(request):
        return HttpResponseRedirect('/main')
    block_id = request.GET['block_id']
    if not check_permission_admin(request.user.username, block_id):
        return HttpResponseRedirect('/main')
    if request.method == 'POST':
        connector, cursor = open_db()
        opened = 1 if 'opened' in request.POST.keys() else 0
        time_start = request.POST['time_start'].replace('T', ' ') + ':00'
        time_end = request.POST['time_end'].replace('T', ' ') + ':59'
        cursor.execute('UPDATE Blocks SET time_start = ?, time_end = ?, opened = ? WHERE id = ?',
                       (time_start, time_end, opened, block_id))
        close_db(connector)
        return HttpResponseRedirect('/admin/block?block_id=' + str(block_id))
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Blocks WHERE id = ?', (block_id,))
    block = cursor.fetchone()
    close_db(connector)
    return render(request, "blocks_settings.html",
                  context={"name": block[1],
                           'tasks': admin_tasks_table(request.GET['block_id']),
                           'block_id': request.GET['block_id'],
                           'is_superuser': check_teacher(request),
                           'opened': 'checked' if block[5] else '',
                           'time_start': block[3].replace(' ', 'T')[:-3],
                           'time_end': block[4].replace(' ', 'T')[:-3]})


def task_settings(request):
    if not check_assistant(request):
        return HttpResponseRedirect('/main')
    connector, cursor = open_db()
    task_id = request.GET['task_id']
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (task_id,))
    this_task = cursor.fetchone()
    cursor.execute('SELECT block_name from Blocks WHERE id = ?', (this_task[2],))
    block_name = cursor.fetchone()[0]
    if not check_permission_admin(request.user.username, this_task[2]):
        return HttpResponseRedirect('/main')
    context = {'block': block_name, 'task': this_task[1], 'legend': this_task[3], 'input': this_task[4],
               'output': this_task[5], 'specifications': this_task[6], 'tests_uploaded': task_has_tests(task_id),
               'tests': forms.TestsForm(), 'block_id': this_task[2], 'task_id': task_id,
               'is_superuser': check_teacher(request)}
    if request.method == 'POST':
        have_tests = int('tests' in request.FILES.keys())
        cursor.execute("UPDATE Tasks SET "
                       "legend = ?, "
                       "input = ?, "
                       "output = ?, "
                       "specifications = ? "
                       "WHERE id = ?;",
                       (request.POST['legend'],
                        request.POST['input'],
                        request.POST['output'],
                        request.POST['specifications'],
                        request.GET['task_id']))
        from os import system
        if have_tests:
            file = request.FILES['tests']
            context['tests_uploaded'] = True
            test_file = '../data/tests/' + str(this_task[0]) + '.dll'
            system('touch ' + test_file)
            with open(test_file, 'wb+') as fs:
                for chunk in file.chunks():
                    fs.write(chunk)
        close_db(connector)
        return HttpResponseRedirect('/admin/task?task_id=' + request.GET['task_id'])
    return render(request, 'task_settings.html', context=context)


def new_task(request):
    if not check_teacher(request) or not check_permission_admin(request.user.username, request.GET['block_id']):
        return HttpResponseRedirect('/main')
    connector, cursor = open_db()
    cursor.execute('SELECT block_name FROM Blocks WHERE id = ?', (request.GET['block_id'],))
    block_name = cursor.fetchone()[0]
    if request.method == 'GET':
        return render(request, 'new_task.html', context={'form': forms.NewTaskForm(),
                                                               'name': block_name,
                                                               'block_id': request.GET['block_id']})
    else:
        task_name = request.POST['name']
        cursor.execute('SELECT * FROM Tasks')
        full = cursor.fetchall()
        index = full[-1][0] + 1 if full else 1
        cursor.execute("INSERT INTO Tasks VALUES (?, ?, ?, ?, ?, ?, ?)", (index,
                                                                             task_name,
                                                                             request.GET['block_id'],
                                                                             '',
                                                                             '',
                                                                             '',
                                                                             ''))
        close_db(connector)
        return HttpResponseRedirect('/admin/task?task_id=' + str(index))


def admin(request):
    if not check_assistant(request):
        return HttpResponseRedirect('/main')
    return render(request, "admin.html", context={"blocks": admin_blocks_table(request),
                                                  'is_superuser': check_god(request)})


def main(request):
    if not check_login(request):
        return HttpResponseRedirect('/enter')
    return render(request, "main.html", context={"blocks": blocks_table(request),
                                                 'is_admin': check_assistant(request)})


def redirect(request):
    return HttpResponseRedirect('/main')


def block(request):
    if not check_login(request) or not check_permission_student(request.user.username, request.GET['block_id']):
        return HttpResponseRedirect('/enter')
    connector, cursor = open_db()
    cursor.execute('SELECT block_name FROM Blocks WHERE id = ?', (request.GET['block_id'],))
    name = cursor.fetchone()[0]
    return render(request, "block.html", context={"name": name,
                                                        'tasks': tasks_table(request.GET['block_id']),
                                                        'is_admin': check_assistant(request)})


def task(request):
    if not check_login(request):
        return HttpResponseRedirect('/enter')
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE id = ?', (request.GET['task_id'],))
    this_task = cursor.fetchone()
    cursor.execute('SELECT block_name FROM Blocks WHERE id = ?', (this_task[2],))
    block_name = cursor.fetchone()[0]
    close_db(connector)
    if not check_permission_student(request.user.username, this_task[2]):
        return HttpResponseRedirect('/main')
    if request.method == 'GET':
        context = {
            'block_name': block_name,
            'task_name': this_task[1],
            'legend': this_task[3].replace('\n', '<br>'),
            'input': this_task[4].replace('\n', '<br>'),
            'output': this_task[5].replace('\n', '<br>'),
            'specifications': this_task[6].replace('\n', '<br>'),
            'form': forms.FileForm(),
            'solutions': task_solutions_table(this_task[0], request.user.username),
            'block_id': this_task[2],
            'is_admin': check_assistant(request)
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
    if not check_login(request):
        return HttpResponseRedirect('/enter')
    context = {'is_admin': check_assistant(request)}
    if request.method == 'POST':
        old = request.POST['old']
        new = request.POST['new']
        again = request.POST['again']
        username = request.user.username
        user = authenticate(username=username, password=old)
        if user is None:
            context['error'] = 'Неверный пароль'
        elif new != again:
            context['error'] = 'Пароли не совпадают'
        else:
            user.set_password(new)
            user.save()
            context['error'] = 'Пароль успешно изменен'
            user = authenticate(username=username, password=new)
            if user is not None and user.is_active:
                login(request, user)
                request.session['is_auth_ok'] = '1'
    return render(request, 'settings.html', context=context)


def reset_password(request):
    code = request.GET['code']
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Restores WHERE code = ?', (code,))
    pair = cursor.fetchone()
    if not pair:
        return HttpResponseRedirect('/enter')
    if request.method == 'GET':
        return render(request, 'reset_password.html')
    else:
        if request.POST['password'] != request.POST['again']:
            return render(request, 'reset_password.html', context={'error': 'Пароли не совпадают'})
        else:
            user = User.objects.get(username=pair[1])
            user.set_password(request.POST['password'])
            user.save()
            cursor.execute('DELETE FROM Restores WHERE email = ?', (pair[1],))
            close_db(connector)
            return HttpResponseRedirect('/enter')


def restore(request):
    if check_login(request):
        return HttpResponseRedirect("/main")
    elif request.method == 'GET':
        return render(request, 'restore.html')
    else:
        email = request.POST['email']
        connector, cursor = open_db()
        cursor.execute('SELECT * FROM Users WHERE email = ?', (email,))
        if not cursor.fetchone():
            return HttpResponseRedirect('/enter')
        cursor.execute('SELECT * FROM Restores WHERE email = ?', (email,))
        if cursor.fetchone():
            return HttpResponseRedirect('/enter')
        h = get_restore_hash()
        cursor.execute('INSERT INTO Restores VALUES (?, ?)', (h, email))
        close_db(connector)
        send_email('Reset password',
                   email,
                   'seblockssender@gmail.com',
                   'Restore your password using this link:\nhttp://mathwave.pythonanywhere.com/reset_password?code=' + h)
    return HttpResponseRedirect('/enter')


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


def registration(request):
    error = ''
    if request.method == 'POST':
        connector, cursor = open_db()
        cursor.execute('SELECT * FROM Users WHERE email = ?', (request.POST['email'],))
        if cursor.fetchone():
            error = 'Пользователь с таким email уже существует'
        elif request.POST['password'] != request.POST['again']:
            error = 'Пароли не совпадают'
        else:
            cursor.execute('INSERT INTO Users VALUES (?, ?, ?, ?, ?)', (
                request.POST['surname'],
                request.POST['name'],
                request.POST['middle_name'],
                request.POST['group_name'],
                request.POST['email']
            ))
            close_db(connector)
            user = User.objects.create(username=request.POST['email'])
            user.set_password(request.POST['password'])
            user.save()
            return HttpResponseRedirect('/enter')
    return render(request, 'registration.html', context={'error': error})


def delete_course(request):
    if not check_god(request):
        return HttpResponseRedirect('/main')
    course_id = request.GET['course_id']
    delete_course_extra(course_id)
    return HttpResponseRedirect('/superuser/main')


def exit(request):
    logout(request)
    request.session["is_auth_ok"] = '0'
    return HttpResponseRedirect('/enter')


def reset(request):
    if request.GET['password'] != 'helloworld':
        return HttpResponseRedirect('/main')
    connector, cursor = open_db()
    cursor.execute('DROP TABLE IF EXISTS Courses;')
    cursor.execute('DROP TABLE IF EXISTS Blocks;')
    cursor.execute('DROP TABLE IF EXISTS Tasks;')
    cursor.execute('DROP TABLE IF EXISTS Users;')
    cursor.execute('DROP TABLE IF EXISTS Solutions;')
    cursor.execute('DROP TABLE IF EXISTS Subscribes;')
    cursor.execute('DROP TABLE IF EXISTS Restores;')
    cursor.execute('DROP TABLE IF EXISTS Marks;')
    cursor.execute('DELETE FROM auth_user WHERE username != "admin"')
    cursor.execute(
        '''
        CREATE TABLE Courses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT
        );
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE Blocks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_name TEXT,
            course_id INTEGER,
            time_start TEXT,
            time_end TEXT,
            opened INTEGER
        );
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE Tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            block_id INTEGER,
            legend TEXT,
            input TEXT,
            output TEXT,
            specifications TEXT
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
            email TEXT
        );
        '''
    )
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
        CREATE TABLE Restores(
            code TEXT,
            email TEXT
        );
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE Subscribes(
            username TEXT,
            course_id TEXT,
            is_assistant INTEGER
        );
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE Marks(
            username TEXT,
            block_id INTEGER,
            mark INTEGER
        );
        '''
    )
    cursor.execute('INSERT INTO Users VALUES ("admin", "admin", "admin", "admin_group", "admin");')
    close_db(connector)
    from os import system
    from os.path import exists
    if exists('../data'):
        system('rm -r ../data')
    system('mkdir ../data')
    system('mkdir ../data/solutions')
    system('mkdir ../data/tests')
    system('mkdir ../data/collecting_dir')
    return HttpResponseRedirect('/main')
