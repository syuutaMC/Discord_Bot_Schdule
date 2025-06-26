from dao_sqlite3 import dao_sqlite3
import sqlite3
import pandas as pd

dbname = 'discord_schedule.db'
conn = sqlite3.connect(dbname)
# sqliteを操作するカーソルオブジェクトを作成
connection = conn.cursor()

db = dao_sqlite3()

db.select_all()