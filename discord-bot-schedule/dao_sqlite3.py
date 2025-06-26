import sqlite3

class dao_sqlite3(object):
    def __init__(self):
        self.dbname = 'discord_schedule.db'
        self.tablename = 'schedule'
        self._conn = None
        self._curs = None
        self._conn_db()

    # DBの接続管理
    def _conn_db(self):
        self._conn = sqlite3.connect(self.dbname)
        self._curs = self._conn.cursor()

    def _close_db(self):
        self._conn.close()


    def insert_event(self, event_id, channel_id, role_id):
        self._curs.execute(f'INSERT INTO {self.tablename} VALUES({event_id},{channel_id},{role_id})')
        self._conn.commit()
        print('* insert data ')

    def update_name(self, table_name, new_name, pre_name):
        self._curs.execute('UPDATE '+ table_name +' set name = "' + new_name + '" WHERE name = "' + pre_name + '"')
        self._conn.commit()
        print('* update data')

    def select_all(self):
        self._curs.execute('SELECT * FROM ' + self.tablename)
        for row in self._curs:
            print(row)

    def get_role_id(self, event_id):
        self._curs.execute(f'SELECT role_id FROM {self.tablename} WHERE event_id = {event_id}')
        result = self._curs.fetchone()[0]
        return result
    
    def get_channel_id(self, event_id):
        self._curs.execute(f'SELECT channel_id FROM {self.tablename} WHERE event_id = {event_id}')
        result = self._curs.fetchone()[0]
        return result