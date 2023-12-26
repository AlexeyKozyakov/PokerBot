import datetime

from peewee import *

db = SqliteDatabase('poker.db')


class BaseModel(Model):
    class Meta:
        database = db


class Game(BaseModel):
    chat_id = CharField()
    is_finished = BooleanField()


class BuyIn(BaseModel):
    game = ForeignKeyField(Game, backref="buy_ins")
    user = CharField()
    amount = IntegerField()
    timestamp = DateTimeField(default=datetime.datetime.now)


class CashOut(BaseModel):
    game = ForeignKeyField(Game, backref="cash_outs")
    user = CharField()
    amount = IntegerField()
    timestamp = DateTimeField(default=datetime.datetime.now)


Game.create_table()
BuyIn.create_table()
CashOut.create_table()
