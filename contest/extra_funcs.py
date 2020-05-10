from subprocess import Popen
from django.contrib.auth.models import User


def shell(command, timeout=None):
    p = Popen(command, shell=True)
    p.wait(timeout)
    p.kill()


def open_db():
    from sqlite3 import connect
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    return connector, cursor


def close_db(connector):
    connector.commit()
    connector.close()


def random_string():
    from random import choice
    letters = 'qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBNM'
    password = ''
    for i in range(20):
        password += choice(letters)
    return password


def get_restore_hash():
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Restores')
    available = [a[0] for a in cursor.fetchall()]
    while True:
        s = random_string()
        if s not in available:
            break
    return s


def task_has_tests(task_id):
    from os.path import exists
    return exists('../data/tests/' + str(task_id) + '.dll')


def check_login(request):
    return request.user.is_authenticated


def is_assistant(username):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Subscribes WHERE username = ? AND is_assistant != 0', (username,))
    l = cursor.fetchall()
    close_db(connector)
    return len(l) > 0


def check_assistant(request):
    if not check_login(request):
        return False
    if request.user.is_staff:
        return True
    return is_assistant(request.user.username)


def check_teacher(request):
    return request.user.is_staff


def check_god(request):
    return request.user.is_superuser


def check_subscription_block(username, block_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Subscribes INNER JOIN Blocks ON Blocks.course_id = Subscribes.course_id'
                   ' WHERE id = ? AND username = ?', (block_id, username))
    l = cursor.fetchall()
    close_db(connector)
    return len(l) > 0


def check_permission_admin(username, block_id):
    user = User.objects.get(username=username)
    if not user:
        return False
    if user.is_superuser:
        return True
    if not check_subscription_block(username, block_id):
        result = False
    else:
        if user.is_staff:
            result = True
        else:
            connector, cursor = open_db()
            cursor.execute('SELECT * FROM Subscribes INNER JOIN Blocks ON Subscribes.course_id = Blocks.course_id '
                           'WHERE username = ? AND id = ? AND is_assistant = 1', (username, block_id))
            l = cursor.fetchall()
            if l:
                result = True
            else:
                result = False
            close_db(connector)
    return result


def dt(line):
    date, time = line.split(' ')
    date = list(map(int, date.split('-')))
    time = list(map(int, time.split(':')))
    from datetime import datetime, timedelta
    return datetime(*date, hour=time[0], minute=time[1], second=time[2]) - timedelta(hours=3)


def check_permission_student(username, block_id):
    if check_permission_admin(username, block_id):
        return True
    if not check_subscription_block(username, block_id):
        return False
    connector, cursor = open_db()
    cursor.execute('SELECT opened, time_start, time_end FROM Blocks WHERE id = ?', (block_id,))
    result = cursor.fetchone()
    close_db(connector)
    try:
        from datetime import datetime
        return result[0] and dt(result[1]) <= datetime.now() <= dt(result[2])
    except:
        return False


def check_permission_course(username, course_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Subscribes WHERE username = ? AND course_id = ?', (username, course_id))
    l = cursor.fetchall()
    close_db(connector)
    return len(l) > 0


def send(subject, to_addr, from_addr, body_text):
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


def send_email(subject, to_addr, from_addr, body_text):
    from threading import Thread
    Thread(target=lambda: send(subject, to_addr, from_addr, body_text)).start()


def delete_task_extra(task_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions WHERE task_id = ?', (task_id,))
    solutions_ids = [s[0] for s in cursor.fetchall()]
    cursor.execute('DELETE FROM Solutions WHERE task_id = ?', (task_id,))
    cursor.execute('DELETE FROM Tasks WHERE id = ?', (task_id,))
    close_db(connector)
    from shutil import rmtree
    from os import remove
    for i in solutions_ids:
        rmtree('../data/solutions/' + str(i))
    if task_has_tests(task_id):
        remove('../data/tests/' + str(task_id) + '.dll')


def delete_block_extra(block_id):
    connector, cursor = open_db()
    cursor.execute('DELETE FROM Blocks WHERE id = ?', (block_id,))
    cursor.execute('DELETE FROM Marks WHERE block_id = ?', (block_id,))
    cursor.execute('SELECT * FROM Tasks WHERE block_id = ?', (block_id,))
    task_ids = [i[0] for i in cursor.fetchall()]
    close_db(connector)
    for task_id in task_ids:
        delete_task_extra(task_id)


def delete_course_extra(course_id):
    connector, cursor = open_db()
    cursor.execute('DELETE FROM Subscribes WHERE course_id = ?;', (course_id,))
    cursor.execute('DELETE FROM Courses WHERE id = ?', (course_id,))
    cursor.execute('SELECT id FROM Blocks WHERE course_id = ?;', (course_id,))
    block_ids = [i[0] for i in cursor.fetchall()]
    close_db(connector)
    for block_id in block_ids:
        delete_block_extra(block_id)


def available_blocks(username, role):
    connector, cursor = open_db()
    showable = {}
    cursor.execute('SELECT * FROM Courses '
                   'INNER JOIN Subscribes ON Subscribes.course_id = Courses.id '
                   'WHERE username = ?', (username,))
    for node in cursor.fetchall():
        showable[(node[0], node[1])] = []
    cursor.execute('SELECT Blocks.id, Blocks.block_name, Courses.id, Courses.course_name FROM Blocks '
                   'INNER JOIN Courses ON Courses.id = Blocks.course_id '
                   'INNER JOIN Subscribes ON Subscribes.course_id = Courses.id '
                   'WHERE username = ?', (username,))
    l = cursor.fetchall()
    close_db(connector)
    for node in l:
        if role == 0:
            if check_permission_student(username, node[0]):
                showable[(node[-2], node[-1])].append((node[0], node[1]))
        else:
            if check_permission_admin(username, node[0]):
                showable[(node[-2], node[-1])].append((node[0], node[1]))
    return showable


def set_mark(solution_id, mark):
    connector, cursor = open_db()
    cursor.execute(
        'SELECT Tasks.block_id, Solutions.username FROM Solutions '
        'INNER JOIN Tasks ON Tasks.id = Solutions.task_id '
        'WHERE Solutions.id = ?', (solution_id,)
    )
    block_id, username = cursor.fetchone()
    cursor.execute('UPDATE Marks SET mark = ? WHERE username = ? AND block_id = ?',
                   (mark, username, block_id))
    close_db(connector)


def list_find(arr, predicate):
    findable = []
    for i in range(len(arr)):
        if predicate(arr[i]):
            findable.append(i)
    return findable


def solutions_by_request(request):
    connector, cursor = open_db()
    cursor.execute(
        'SELECT A.id, B.id, B.task_name, C.email, C.group_name, '
        'C.surname || " " || C.name || " " || C.middle_name, '
        'A.result, D.mark FROM Solutions AS A '
        'INNER JOIN Tasks AS B ON A.task_id = B.id '
        'INNER JOIN Users AS C ON A.username = C.email '
        'INNER JOIN Marks AS D ON D.username = A.username '
        'AND D.block_id = B.block_id '
        'WHERE B.block_id = ?', (int(request['block_id']),)
    )
    solutions = cursor.fetchall()
    allowed = ['user', 'task_name', 'group']
    solutions_json = [
        {
            'solution_id': solutions[i][0],
            'task_id': solutions[i][1],
            'task_name': solutions[i][2],
            'username': solutions[i][3],
            'group': solutions[i][4],
            'user': solutions[i][5],
            'result': solutions[i][6],
            'mark': solutions[i][7]
        }
        for i in range(len(solutions))
    ]
    my_request = {key: request[key] for key in request.keys() if key != 'block_id'}
    for key in my_request.keys():
        if key in allowed:
            solutions_json = [solution for solution in solutions_json if solution[key] == my_request[key]]
    user_task = {(u['username'], u['task_id']): 0 for u in solutions_json}
    if 'best_result' in request.keys():
        for solution in solutions_json:
            if int(solution['result'].split('/')[0]) > user_task[(solution['username'], solution['task_id'])]:
                user_task[(solution['username'], solution['task_id'])] = int(solution['result'].split('/')[0])
        solutions_json = [
            solution for solution in solutions_json
            if int(solution['result'].split('/')[0]) == user_task[(solution['username'], solution['task_id'])]
        ]
    if 'last_solution' in request.keys():
        for u_t in user_task.keys():
            found = list_find(solutions_json, lambda elem: elem['username'] == u_t[0] and elem['task_id'] == u_t[1])
            for i in range(1, len(found)):
                solutions_json.pop(len(found) - 1 - i)
    return solutions_json


def get_files(path):
    from os import listdir
    from os.path import isfile, join
    files_dict = {}
    for file in listdir(path):
        current_file = join(path, file)
        if isfile(current_file):
            if not current_file.endswith('.csproj') and not current_file.endswith('.sln'):
                try:
                    files_dict['/'.join(current_file.split('/')[4:])] = open(current_file, 'r').read()
                except:
                    pass
        else:
            files_dict = {**files_dict, **get_files(current_file)}
    return files_dict


def get_req(request):
    return ('&' + '&'.join(str(x) + '=' + str(request[x]) for x in request.keys())) if request else ''


def is_integer(line):
    ret = True
    try:
        int(line)
    except:
        ret = False
    return ret
