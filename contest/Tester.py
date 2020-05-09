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
    tag = doc.getElementsByTagName('test-run')[0]
    passed, total = tag.getAttribute('passed'), tag.getAttribute('total')
    if not passed or not total:
        res = 'Test failure'
    else:
        res = passed + '/' + total
    connector, cursor = open_db()
    cursor.execute("UPDATE Solutions SET result = ? WHERE id = ?;", (res, solution_id))
    close_db(connector)


class Tester(Thread):

    def __init__(self, solution_id, task_id, working_dir):
        Thread.__init__(self)
        self.solution_id = solution_id
        self.task_id = task_id
        self.working_dir = working_dir

    def run(self):
        test(self.solution_id, self.task_id, self.working_dir)
