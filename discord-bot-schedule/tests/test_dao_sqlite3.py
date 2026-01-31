import os
import sqlite3
import tempfile
import unittest

from dao_sqlite3 import dao_sqlite3


class TestDaoSqlite3(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE schedule (
                event_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL
            );
            """
        )
        conn.commit()
        conn.close()
        self.db = dao_sqlite3(dbname=self.db_path)

    def tearDown(self):
        if hasattr(self, "db"):
            self.db._close_db()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_insert_get_list_update_delete(self):
        self.db.insert_event(1, 10, 100)
        self.db.insert_event(2, 20, 200)

        self.assertEqual(self.db.get_channel_id(1), 10)
        self.assertEqual(self.db.get_role_id(2), 200)

        records = self.db.list_events()
        self.assertEqual(len(records), 2)

        self.db.update_event(1, 11, 111)
        self.assertEqual(self.db.get_channel_id(1), 11)
        self.assertEqual(self.db.get_role_id(1), 111)

        self.db.delete_event(2)
        self.assertIsNone(self.db.get_event(2))

    def test_missing_event_returns_none(self):
        self.assertIsNone(self.db.get_channel_id(999))
        self.assertIsNone(self.db.get_role_id(999))
        self.assertIsNone(self.db.get_event(999))


if __name__ == "__main__":
    unittest.main()
