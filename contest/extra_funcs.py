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


def check_assistant(request):
    if not check_login(request):
        return False
    if request.user.is_staff:
        return True
    connector, cursor = open_db()
    cursor.execute('SELECT * FROM Subscribes WHERE username = ? AND is_assistant != 0', (request.user.username,))
    l = cursor.fetchall()
    close_db(connector)
    return len(l) > 0


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


def check_permission_student(username, block_id):
    if check_permission_admin(username, block_id):
        return True
    if not check_subscription_block(username, block_id):
        return False
    connector, cursor = open_db()
    cursor.execute('SELECT opened, time_start, time_end FROM Blocks WHERE id = ?', (block_id,))
    result = cursor.fetchone()
    close_db(connector)
    from datetime import datetime
    return result[0] and result[1] <= str(datetime.now()) <= result[2]


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
    server.login('seblockssender@gmail.com', 'HSEguestHSEpassw0rd')
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
    cursor.execute('SELECT * FROM Courses INNER JOIN Subscribes ON Subscribes.course_id = Courses.id WHERE username = ?', (username,))
    for node in cursor.fetchall():
        showable[(node[0], node[1])] = []
    cursor.execute('SELECT * FROM Blocks INNER JOIN Courses ON Courses.id = Blocks.course_id')
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
