import datetime as dt

import peewee as pw
from playhouse.postgres_ext import DateTimeTZField

from .db import BaseModel


class User(BaseModel):
    username = pw.CharField(unique=True)
    email = pw.CharField(unique=True)
    first_name = pw.CharField(null=True)
    last_name = pw.CharField(null=True)
    patronymic = pw.CharField(null=True)


class WaitMeetingQueue(BaseModel):
    user = pw.ForeignKeyField(User, primary_key=True)
    created_at = DateTimeTZField(
        default=dt.datetime.now,
    )


class Meeting(BaseModel):
    usr1 = pw.ForeignKeyField(User, backref='usr1')
    usr2 = pw.ForeignKeyField(User, backref='usr2')
    started_at = DateTimeTZField()
    end_at = DateTimeTZField()
    created_at = DateTimeTZField(
        default=dt.datetime.now,
    )
