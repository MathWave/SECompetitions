from threading import Thread
from sqlite3 import connect


class TesterGlobal(Thread):

    def run(self):
        connector = connect('db.sqlite3')
        cursor = connector.cursor()
        from contest.Tester import Tester
        thread = Tester(self.competition_name, self.task_name, self.index)
        thread.start()
        thread.join(self.time_limit_milliseconds / 1000)
        cursor.execute('SELECT * FROM Solutions WHERE id = ?', (self.index,))
        if cursor.fetchone()[4] == 'TESTING':
            cursor.execute("UPDATE Solutions SET result = 'Time limit' WHERE id = ?;", (self.index,))
        connector.commit()
        cursor.close()
        connector.close()

    def __init__(self, competition_name, task_name, index, time_limit_milliseconds):
        Thread.__init__(self)
        self.competition_name = competition_name
        self.task_name = task_name
        self.index = index
        self.time_limit_milliseconds = time_limit_milliseconds
