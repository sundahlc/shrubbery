import pandas as pd
from datetime import datetime
import psycopg2
import urllib.parse
import os
from random import choice
from time import sleep


class db_talker():
    '''
    Usage:
    with db_talker() as cur:
        cur.execute(...)
    Automatically closes at the end of with block.
    '''

    def __enter__(self):
        self.conn = self.connect_to_elephantsql()
        self.cur = self.conn.cursor()
        return self.cur

    def __exit__(self, *args):
        self.conn.commit()
        self.conn.close()

    def connect_to_elephantsql(self):
        # Connect to ElephantSQL database
        urllib.parse.uses_netloc.append("postgres")
        try:
            DATABASE_URL = os.environ['DATABASE_URL']
        except KeyError:
            DATABASE_URL = open(r'../shrubbery_login.txt', 'r').read().strip()
        url = urllib.parse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(database=url.path[1:],
        user = url.username,
        password = url.password,
        host = url.hostname,
        port = url.port
        )

        return conn

with db_talker() as cur:
    cur.execute("select contents from cards where type='agenda'")
    agendas = cur.fetchall()
    cur.execute("select name from players")
    players = cur.fetchall()
    cur.execute("update players set agenda=null")

    for player in players:
        assigned_agenda = choice(agendas)
        agendas.remove(assigned_agenda)
        cur.execute(f"update players set agenda='{assigned_agenda[0]}' where name='{player[0]}'")