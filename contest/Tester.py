from threading import Thread
from sqlite3 import connect


def test(competition, task, id):
    path = '../competitions/' + competition + '/solutions/' + task + '/' + str(id) + '/' + task + '/'
    from os import system, remove, mkdir
    from os.path import exists, abspath
    system('rm -r' + path + 'bin/Release')
    mkdir(path + 'bin/Release')
    system('xbuild /p:Configuration=Release ' + path + task + '.csproj')
    tests_path = '../competitions/' + competition + '/tasks/' + task + '/tests/'
    with open(path + 'bin/Release/results.txt', 'w') as fs:
        fs.write('OK')
    if exists(path + 'bin/Release/' + task + '.exe'):
        pass
    # oh shit, now we should start testing
    else:
        connector = connect('db.sqlite3')
        cursor = connector.cursor()
        cursor.execute("UPDATE Solutions SET result = 'CE' WHERE id = ?", (id,))
        connector.commit()
        cursor.close()
        connector.close()


class Tester(Thread):
    def __init__(self, competition_name, task_name, index):
        Thread.__init__(self)
        self.competition_name = competition_name
        self.task_name = task_name
        self.index = index

    def run(self):
        test(self.competition_name, self.task_name, self.index)


########################################################################################################################

# test_count = 1
# current_test = tests_path + str(test_count).zfill(2)
# while exists(current_test) and \
#         open(path + 'bin/Release/results.txt', 'r').read() == "OK":
#     command = 'mono64 tester.exe ' + abspath(path + 'bin/Release/' + task + '.exe') + ' ' +\
#               abspath(current_test) + ' ' + abspath(current_test + '.a') + ' ' + str(10000)
#     res = system(command)
#     res = res
