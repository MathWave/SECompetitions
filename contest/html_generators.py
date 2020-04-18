from contest.extra_funcs import *


def users_sorting_key(x):
    return ' '.join(x[0:3])


def get_new_user_inputs():
    values = ['surname', 'name', 'middle_name', 'group_name', 'email']
    line = '<tr>'
    for val in values:
        line += '<td><input type="text" name="' + val + '"></td>'
    line += '<td></td><td><input type="submit" value="Создать">'
    return line


def user_role(value):
    if value == 0:
        return 'Студент'
    elif value == 1:
        return 'Ассистент'
    elif value == 2:
        return 'Преподаватель'
    else:
        return 'Бог'


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
        for field in range(5):
            line += '<td>' + user[field] + '</td>'
        line += '<td>' + user_role(user[5]) + '</td>'
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


# получить список соревнований
def admin_competitions_table(request):
    connector, cursor = open_db()
    if check_teacher(request):
        cursor.execute("SELECT * FROM Competitions")
    else:
        cursor.execute("SELECT * FROM Competitions INNER JOIN Permissions ON "
                       "Competitions.id = Permissions.competition_id WHERE username = ?;", (request.user.username,))
    comps = cursor.fetchall()
    line = '<table>\n'
    for c in comps:
        line += '<tr><td><a href="http://192.168.1.8:8000/admin/competition?competition_id=' + str(c[0]) + '">' + c[
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
        line += '<tr><td><a href="http://192.168.1.8:8000/admin/task?task_id=' + str(c[0]) + '">' + c[1] + '</td></tr>\n'
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
        table += "<td><a href='http://192.168.1.8:8000/admin/solution?solution_id=" + str(solution[0]) + "'>" + \
                 str(solution[0]) + '</a></td>'
        table += '<td>' + str(solution[5]) + '</td>\n'
        table += '<td>' + ' '.join(solution[12:15]) + '</td>'
        table += '<td>' + str(solution[3]) + '</td>'
        table += '</tr>\n'
    return table


def permissions_table(competition_id):
    line = '<tr><td><input type="text" name="input"></td><td><input type="submit" value="Добавить"></td></tr>'
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Permissions AS A INNER JOIN Users AS B ON '
                   'A.username = B.email WHERE competition_id = ?;', (competition_id,))
    perms = cursor.fetchall()
    close_db(connector)
    for perm in perms:
        line += '<tr><td>' + ' '.join(perm[3:6]) + '</td><td>' + perm[6] + '</td></tr>'
    return line


# получить список всех соревнований (потом надо будет сделать фильтр)
def competitions_table(request):
    connector, cursor = open_db()
    if check_teacher(request):
        cursor.execute("SELECT * FROM Competitions")
    else:
        cursor.execute("SELECT * FROM Competitions INNER JOIN Permissions ON "
                       "Competitions.id = Permissions.competition_id WHERE username = ?;", (request.user.username,))
    comps = cursor.fetchall()
    line = '<table>\n'
    for c in comps:
        line += '<tr><td><a href="http://192.168.1.8:8000/competition?competition_id=' + str(c[0]) + '">' + c[
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
        line += '<tr><td><a href="http://192.168.1.8:8000/task?task_id=' + str(c[0]) + '">' + c[1] + \
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