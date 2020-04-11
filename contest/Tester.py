from threading import Thread


def test(solution_id, task_id, working_dir):
    from subprocess import Popen
    from os.path import join
    from contest.extra_funcs import open_db, close_db
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
