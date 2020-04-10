from threading import Thread
from shutil import rmtree


def test_folder_name(path):
    from os import listdir
    name = 'test_folder'
    if name not in listdir(path):
        return name
    add = 0
    while name + str(add) in listdir(path):
        add += 1
    return name + str(add)


def solution_path(path):
    print(path)
    from os import listdir
    from os.path import isdir, join
    files = [x for x in listdir(path) if '.sln' in x and not x.startswith('.')]
    if files:
        return path
    return ''.join([solution_path(join(path, file)) for file in listdir(path) if isdir(join(path, file))])


def is_project(path):
    from os import listdir
    from os.path import abspath
    for file in listdir(abspath(path)):
        if '.csproj' in file:
            return True
    return False


def build_and_copy(path, working_dir):
    from os.path import exists, join
    from contest.methods import shell
    name = path.split('/')[-1]
    rm_dir = path + '/bin/Debug'
    rmtree(rm_dir)
    print('before msbuild')
    msbuild_cmd = 'msbuild ' + path + '/' + name + '.csproj /p:Configuration=Debug'
    print(msbuild_cmd)
    shell(msbuild_cmd)
    print('after msbuild')
    for file in name + '.exe', name + '.pdb':
        if exists(join(path, 'bin/Debug', file)):
            shell('cp -r ' + path + '/bin/Debug/' + file + ' ' + working_dir)
        else:
            return False
    return True


class TesterGlobal(Thread):

    def run(self):
        sln_path = solution_path('../data/solutions/' + str(self.solution_id))
        dll_path = '../data/tests/' + str(self.task_id) + '.dll'
        from os import system, listdir, mkdir
        from os.path import join, isdir
        from shutil import copyfile
        from contest.methods import shell, open_db, close_db
        working_dir = join(sln_path, test_folder_name(sln_path))
        mkdir(working_dir)
        copyfile(dll_path, join(working_dir, str(self.task_id) + '.dll'))
        for project in listdir(sln_path):
            project = join(sln_path, project)
            if isdir(project) and is_project(project):
                if not build_and_copy(project, working_dir):
                    connector, cursor = open_db()
                    cursor.execute("UPDATE Solutions SET result = 'Compilation error' WHERE id = ?;",
                                   (self.solution_id,))
                    close_db(connector)
                    return
        from contest.Tester import Tester
        for file in listdir('nunit_console'):
            shell('cp nunit_console/' + file + ' ' + working_dir)
        thread = Tester(self.solution_id, self.task_id, working_dir)
        thread.start()
        thread.join(self.time_limit_milliseconds / 1000)
        connector, cursor = open_db()
        cursor.execute('SELECT * FROM Solutions WHERE id = ?;', (self.solution_id,))
        if cursor.fetchone()[3] == 'TESTING':
            cursor.execute("UPDATE Solutions SET result = 'Time limit' WHERE id = ?;", (self.solution_id,))
        close_db(connector)
        rmtree(working_dir)

    def __init__(self, solution_id, task_id, task_name, username, time_limit_milliseconds):
        Thread.__init__(self)
        self.solution_id = solution_id
        self.task_id = task_id
        self.task_name = task_name
        self.username = username
        self.time_limit_milliseconds = time_limit_milliseconds
