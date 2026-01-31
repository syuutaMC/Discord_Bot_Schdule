import sqlite3

dbname = 'discord_schedule.db'
conn = sqlite3.connect(dbname)
# sqliteを操作するカーソルオブジェクトを作成
cur = conn.cursor()

# personsというtableを作成してみる
def select_all(self):
    self._curs.execute('SELECT * FROM ' + self.tablename)
    for row in self._curs:
        print(row)

# データベースへコミット。これで変更が反映される。
conn.commit()
conn.close()