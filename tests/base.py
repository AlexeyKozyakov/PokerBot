import unittest

from peewee import SqliteDatabase


class BaseTestCase(unittest.TestCase):
    def models(self):
        return []

    def setUp(self):
        self.test_db = SqliteDatabase(':memory:')
        self.test_db.bind(self.models(), bind_refs=True, bind_backrefs=True)
        self.test_db.connect()
        self.test_db.create_tables(self.models())

    def tearDown(self):
        self.test_db.drop_tables(self.models())
        self.test_db.close()
