from threading import Thread


def test(solution_id, task_id, working_dir):
    from subprocess import Popen
    from os.path import join
    from contest.methods import open_db, close_db
    test_cmd = '(cd ' + working_dir + ' && ' + \
               'mono ../../../../../SECompetitions/nunit_console/nunit3-console.exe ' + \
               str(task_id) + '.dll)'
    p = Popen(test_cmd, shell=True)
    p.wait()
    p.kill()
    from xml.dom.minidom import parse
    doc = parse(join(working_dir, 'TestResult.xml'))
    res = doc.getElementsByTagName('test-suite')[0].getAttribute('result')
    connector, cursor = open_db()
    cursor.execute("UPDATE Solutions SET result = ? WHERE id = ?;", (res, solution_id))
    close_db(connector)
    a = 5


class Tester(Thread):
    def __init__(self, solution_id, task_id, working_dir):
        Thread.__init__(self)
        self.solution_id = solution_id
        self.task_id = task_id
        self.working_dir = working_dir

    def run(self):
        test(self.solution_id, self.task_id, self.working_dir)


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
