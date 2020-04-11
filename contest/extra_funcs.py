from subprocess import Popen


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
    return len(out) != 0 or is_superuser


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

