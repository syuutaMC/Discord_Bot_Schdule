import sqlite3

dbname = 'discord_schedule.db'
conn = sqlite3.connect(dbname)
# sqliteを操作するカーソルオブジェクトを作成
cur = conn.cursor()

# personsというtableを作成してみる
cur.execute(
    'CREATE TABLE schedule(event_id INTEGER PRIMARY KEY, role_id INTEGER, channel_id INTEGER)'
)

# データベースへコミット。これで変更が反映される。
conn.commit()
conn.close()