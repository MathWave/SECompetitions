from threading import Thread
from sqlite3 import connect


def test_folder_name(path):
    from os import listdir
    name = 'test_folder'
    if name not in listdir(path):
        return name
    add = 0
    while name + str(add) in listdir(path):
        add += 1
    return name + str(add)


def is_project(path):
    from os import listdir
    from os.path import abspath
    for file in listdir(abspath(path)):
        if '.csproj' in file:
            return True
    return False


def build_and_copy(path, working_dir):
    from os import system
    from os.path import exists, join
    name = path.split('/')[-1]
    del_cmd = 'rm -r ' + path + '/bin/Debug'
    system(del_cmd)
    system('xbuild ' + path + '/' + name + '.csproj /p:Configuration=Debug')
    for file in name + '.exe', name + '.pdb':
        if exists(join(path, 'bin/Debug', file)):
            system('cp -r ' + path + '/bin/Debug/' + file + ' ' + working_dir)
        else:
            return False
    return True


class TesterGlobal(Thread):

    def run(self):
        from contest.Tester import Tester
        solution_path = '../data/solutions/' + str(self.solution_id) + '/' + self.task_name + '/'
        dll_path = '../data/tests/' + str(self.task_id) + '.dll'
        from os import system, listdir, mkdir
        from os.path import join, isdir
        working_dir = solution_path + test_folder_name(solution_path)
        mkdir(working_dir)
        cp_command = 'cp -r ' + dll_path + ' ' + working_dir
        system(cp_command)
        from contest.views import open_db, close_db
        for project in listdir(solution_path):
            project = join(solution_path, project)
            if isdir(project) and is_project(project):
                if not build_and_copy(project, working_dir):
                    connector, cursor = open_db()
                    cursor.execute("UPDATE Solutions SET result = 'Compilation error' WHERE id = ?;",
                                   (self.solution_id,))
                    close_db(connector)
                    return
        for file in listdir('nunit_files'):
            system('cp nunit_files/' + file + ' ' + working_dir)
        thread = Tester(self.solution_id, self.task_id, working_dir)
        thread.start()
        thread.join(self.time_limit_milliseconds / 1000)
        connector, cursor = open_db()
        cursor.execute('SELECT * FROM Solutions WHERE id = ?;', (self.solution_id,))
        if cursor.fetchone()[3] == 'TESTING':
            cursor.execute("UPDATE Solutions SET result = 'Time limit' WHERE id = ?;", (self.solution_id,))
        close_db(connector)


    def __init__(self, solution_id, task_id, task_name, username, time_limit_milliseconds):
        Thread.__init__(self)
        self.solution_id = solution_id
        self.task_id = task_id
        self.task_name = task_name
        self.username = username
        self.time_limit_milliseconds = time_limit_milliseconds
