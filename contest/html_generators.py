from contest.extra_funcs import *
from django.contrib.auth.models import User


def teachers_in_course(course_id):
    from sqlite3 import connect
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute('SELECT surname, name, middle_name FROM Users AS A INNER JOIN '
                   'Subscribes AS B ON A.email = B.username INNER JOIN auth_user ON auth_user.username = A.email WHERE course_id = ? AND is_staff = 1;', (course_id,))
    teachers = set(cursor.fetchall())
    close_db(connector)
    return [' '.join(teacher) for teacher in teachers]


def teachers_select():
    connector, cursor = open_db()
    cursor.execute('SELECT username FROM auth_user WHERE is_staff = 1;')
    emails = [t[0] for t in cursor.fetchall()]
    close_db(connector)
    line = '<select name="teacher">'
    for email in sorted(emails):
        line += '<option value="' + email + '">' + email + '</option>'
    line += '</select>'
    return line


def users_select(course_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Subscribes INNER JOIN auth_user ON Subscribes.username = auth_user.username WHERE is_staff != 1 AND course_id = ?;', (course_id,))
    emails = [t[0] for t in cursor.fetchall()]
    close_db(connector)
    line = '<select name="user">'
    for email in sorted(emails):
        line += '<option value="' + email + '">' + email + '</option>'
    line += '</select>'
    return line


def courses_table_create():
    line = '<tr><td><b>id</b></td><td><b>Название</b></td><td><b>Преподаватели</b></td><td></td></tr>'
    line += '<tr><td></td><td><input type="text" name="course_name"></td><td>' + teachers_select() \
            + '</td><td><input type="submit" value="Создать"></td></tr>'
    return line


def courses_table():
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Courses;')
    courses_list = cursor.fetchall()
    line = ''
    for course in courses_list:
        line += '<tr><td>' + str(course[0]) + '</td><td>' + course[1] + '</td><td>' + \
                '<br>'.join(teachers_in_course(course[0])) + \
                '</td><td><button onclick="delete_course(' + \
                str(course[0]) + ')">Удалить</button></td></tr>'
    return line


def users_sorting_key(x):
    return ' '.join(x[0:3])


def user_role(value):
    user = User.objects.get(username=value)
    if user.is_superuser:
        return 'Бог'
    elif user.is_staff:
        return 'Преподаватель'
    elif is_assistant(value):
        return 'Ассистент'
    else:
        return 'Студент'


def all_users():
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Users')
    users = cursor.fetchall()
    close_db(connector)
    return sorted(users, key=users_sorting_key)


def users_in_course(course_id):
    connector, cursor = open_db()
    cursor.execute('SELECT surname, name, middle_name, group_name, email FROM Users INNER JOIN Subscribes ON Users.email = Subscribes.username WHERE course_id = ?', (course_id,))
    users = cursor.fetchall()
    close_db(connector)
    return sorted(users, key=users_sorting_key)


def user_table(course_id=None):
    columns_ru = ['Фамилия', 'Имя', 'Отчество', 'Группа', 'Почта', 'Роль']
    line = '<tr>'
    for c in columns_ru:
        line += '<td><b>' + c + '</b></td>'
    line += '<td></td></tr>'
    if course_id:
        users = users_in_course(course_id)
    else:
        connector, cursor = open_db()
        cursor.execute('SELECT * FROM Users')
        users = cursor.fetchall()
        close_db(connector)
    for user in sorted(users, key=users_sorting_key):
        line += '<tr>'
        for field in range(5):
            line += '<td>' + user[field] + '</td>'
        line += '<td>' + user_role(user[4]) + '</td>'
        if course_id:
            line += '<td><input type="button" onclick="unsubscribe(\'' + user[4] + '\', ' + str(course_id) + ')" value=Отписка></td></tr>'
        else:
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
           '<option value="user">Cтудент</option>' \
           '<option value="teacher">Преподаватель</option>' \
           '</select>'


def role_table():
    columns_ru = ['Пользователь',  'Роль', '']
    line = '<tr>'
    for c in columns_ru:
        line += '<td><b>' + c + '</b></td>'
    line += '<tr><td>' + user_select() + '</td><td>' + role_select() + \
            '</td><td><input type="submit" value="Назначить"></td></tr>'
    return line


# получить список блоков
def admin_blocks_table(request):
    showable = available_blocks(request.user.username, 1)
    line = ''
    for course in showable.keys():
        line += '<h2>' + course[1] + '</h2>\n'
        line += '<table>'
        for block in showable[course]:
            line += '<tr><td><a href="http://192.168.1.8:8000/admin/block?block_id=' + str(block[0]) + '">' + block[1] + '</td></tr>\n'
        line += '</table>\n'
        if check_teacher(request):
            line += '<input type="submit" class="enter_simple" onclick="new_block(' + str(course[0]) + ')" value="Создать новый Блок">\n'
            line += '<button onclick="users_settings(' + str(course[0]) + ')" class="enter_simple">Участники курса</button>\n'
        line += '<hr>'
    return line


def admin_tasks_table(block_id):
    connector, cursor = open_db()
    cursor.execute("SELECT * FROM Tasks WHERE block_id = ?", (block_id,))
    tasks = cursor.fetchall()
    close_db(connector)
    line = '<table>\n'
    for c in tasks:
        line += '<tr><td><a href="http://192.168.1.8:8000/admin/task?task_id=' + str(c[0]) + '">' + c[1] + '</td></tr>\n'
    line += '</table>'
    return line


# посылки для данного блока
def solutions_table(block_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Solutions AS A INNER JOIN Tasks AS B ON A.Task_id = B.id '
                   'INNER JOIN Users AS C ON A.username = C.email WHERE block_id = ?', (block_id,))
    solution_list = cursor.fetchall()
    close_db(connector)
    table = '<tr><td><b>Id</b></td><td><b>Таск</b></td><td><b>Пользователь</b></td><td><b>Вердикт</b></td></tr>'
    for solution in reversed(solution_list):
        table += '<tr>\n'
        table += "<td><a href='http://192.168.1.8:8000/admin/solution?solution_id=" + str(solution[0]) + "'>" + \
                 str(solution[0]) + '</a></td>'
        table += '<td>' + str(solution[5]) + '</td>\n'
        table += '<td>' + ' '.join(solution[12:15]) + '</td>'
        table += '<td>' + str(solution[3]) + '</td>'
        table += '</tr>\n'
    return table


# получить список всех блоков (потом надо будет сделать фильтр)
def blocks_table(request):
    showable = available_blocks(request.user.username, 0)
    line = ''
    for course in showable.keys():
        line += '<h2>' + course[1] + '</h2>\n'
        line += '<table>'
        for block in showable[course]:
            line += '<tr><td><a href="http://192.168.1.8:8000/block?block_id=' + str(block[0]) + '">' + \
                    block[1] + '</td></tr>\n'
        line += '</table>\n'
    return line


# получить таблицу с заданиями из блоки block_name
def tasks_table(block_id):
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Tasks WHERE block_id = ?', (block_id,))
    tasks = cursor.fetchall()
    line = '<table>\n'
    for c in tasks:
        line += '<tr><td><a href="http://192.168.1.8:8000/task?task_id=' + str(c[0]) + '">' + c[1] + \
                '</td></tr>\n'
    line += '</table>'
    return line


# решения отправлен=ые к данному таску конкретным юзером
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