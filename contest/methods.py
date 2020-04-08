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