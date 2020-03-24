from threading import Thread
from sqlite3 import connect


def is_project(path):
    from os import listdir
    from os.path import abspath
    for file in listdir(abspath(path)):
        if '.csproj' in file:
            return True
    return False


def build_and_copy(path):
    from os import system
    from os.path import abspath, dirname, exists, join
    name = path.split('/')[-1]
    del_cmd = 'rm -r ' + path + '/bin/Debug'
    system(del_cmd)
    system('xbuild ' + path + '/' + name + '.csproj /p:Configuration=Debug')
    for file in name + '.exe', name + '.pdb':
        if exists(join(path, 'bin/Debug', file)):
            system('cp -r ' + path + '/bin/Debug/' + file + ' ' + abspath(dirname(abspath(path))) + '/Tests/bin/Debug')
        else:
            return False
    return True


def test(competition, task, id):
    sln_path = '../competitions/' + competition + '/solutions/' + task + '/' + str(id) + ('/' + task) * 2 + '.sln'
    solution_path = '../competitions/' + competition + '/solutions/' + task + '/' + str(id) + '/' + task
    proj_path = '../competitions/' + competition + '/tasks/' + task + '/tests/Tests'
    from os import system, listdir
    from os.path import join, abspath, dirname, isdir
    cp_command = 'cp -r ' + proj_path + ' ' + dirname(sln_path)
    system(cp_command)
    for project in listdir(solution_path):
        project = join(solution_path, project)
        if isdir(project) and project.split('/')[-1] != 'Tests' and is_project(project):
            if not build_and_copy(project):
                connector = connect('db.sqlite3')
                cursor = connector.cursor()
                cursor.execute("UPDATE Solutions SET result = 'Compilation error' WHERE id = ?;", (id,))
                connector.commit()
                cursor.close()
                connector.close()
                return
    test_cmd = '(cd ' + solution_path + ' && ' + \
               'mono ../../../../../../SECompetitions/nunit_console/tools/nunit3-console.exe ' + \
               '/'.join((dirname(sln_path) + '/' + proj_path.split('/')[-1]).split('/')[7:]) + '/bin/Debug/Tests.dll)'
    system(test_cmd)
    from xml.dom.minidom import parse
    doc = parse(join(solution_path, 'TestResult.xml'))
    res = doc.getElementsByTagName('test-suite')[0].getAttribute('result')
    connector = connect('db.sqlite3')
    cursor = connector.cursor()
    cursor.execute("UPDATE Solutions SET result = ? WHERE id = ?;", (res, id))
    connector.commit()
    cursor.close()
    connector.close()
    a = 5
    a += 1


class Tester(Thread):
    def __init__(self, competition_name, task_name, index):
        Thread.__init__(self)
        self.competition_name = competition_name
        self.task_name = task_name
        self.index = index

    def run(self):
        test(self.competition_name, self.task_name, self.index)


########################################################################################################################

    # system('rm -r' + path + 'bin/Release')
    # mkdir(path + 'bin/Release')
    # system('xbuild /p:Configuration=Release ' + path + task + '.csproj')
    # tests_path = '../competitions/' + competition + '/tasks/' + task + '/tests/'
    # with open(path + 'bin/Release/results.txt', 'w') as fs:
    #     fs.write('OK')
    # if exists(path + 'bin/Release/' + task + '.exe'):
    #     pass
    # # oh shit, now we should start testing
    # else:
    #     connector = connect('db.sqlite3')
    #     cursor = connector.cursor()
    #     cursor.execute("UPDATE Solutions SET result = 'CE' WHERE id = ?", (id,))
    #     connector.commit()
    #     cursor.close()
    #     connector.close()

# test_count = 1
# current_test = tests_path + str(test_count).zfill(2)
# while exists(current_test) and \
#         open(path + 'bin/Release/results.txt', 'r').read() == "OK":
#     command = 'mono64 tester.exe ' + abspath(path + 'bin/Release/' + task + '.exe') + ' ' +\
#               abspath(current_test) + ' ' + abspath(current_test + '.a') + ' ' + str(10000)
#     res = system(command)
#     res = res
