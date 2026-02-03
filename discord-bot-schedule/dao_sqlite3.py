import sqlite3

class dao_sqlite3(object):
    def __init__(self, dbname: str = 'discord_schedule.db', tablename: str = 'schedule'):
        self.dbname = dbname
        self.tablename = tablename
        self._conn = None
        self._curs = None
        self._conn_db()
        self._ensure_table()

    # DBの接続管理
    def _conn_db(self):
        self._conn = sqlite3.connect(self.dbname)
        self._curs = self._conn.cursor()

    def _ensure_table(self):
        self._curs.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.tablename} (
                event_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL
            );
            """
        )
        self._conn.commit()

    def _close_db(self):
        self._conn.close()


    def insert_event(self, event_id, channel_id, role_id):
        self._curs.execute(
            f'INSERT INTO {self.tablename} (event_id, channel_id, role_id) VALUES(?, ?, ?)',
            (event_id, channel_id, role_id),
        )
        self._conn.commit()
        print('* insert data ')

    def update_event(self, event_id, channel_id, role_id):
        self._curs.execute(
            f'UPDATE {self.tablename} SET channel_id = ?, role_id = ? WHERE event_id = ?',
            (channel_id, role_id, event_id),
        )
        self._conn.commit()
        print('* update data')

    def update_name(self, table_name, new_name, pre_name):
        self._curs.execute('UPDATE '+ table_name +' set name = "' + new_name + '" WHERE name = "' + pre_name + '"')
        self._conn.commit()
        print('* update data')

    def select_all(self):
        self._curs.execute('SELECT * FROM ' + self.tablename)
        return self._curs.fetchall()

    def list_events(self):
        return self.select_all()

    def get_event(self, event_id):
        self._curs.execute(
            f'SELECT event_id, channel_id, role_id FROM {self.tablename} WHERE event_id = ?',
            (event_id,),
        )
        return self._curs.fetchone()

    def delete_event(self, event_id):
        self._curs.execute(
            f'DELETE FROM {self.tablename} WHERE event_id = ?',
            (event_id,),
        )
        self._conn.commit()
        print('* delete data')

    def get_role_id(self, event_id):
        self._curs.execute(
            f'SELECT role_id FROM {self.tablename} WHERE event_id = ?',
            (event_id,),
        )
        result = self._curs.fetchone()
        return result[0] if result else None
    
    def get_channel_id(self, event_id):
        self._curs.execute(
            f'SELECT channel_id FROM {self.tablename} WHERE event_id = ?',
            (event_id,),
        )
        result = self._curs.fetchone()
        return result[0] if result else None
    

if __name__ == '__main__':
    db = dao_sqlite3()
    print(db.select_all())