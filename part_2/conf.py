import os

RDB_HOST =  os.environ.get('RDB_HOST') or 'localhost'
RDB_PORT = os.environ.get('RDB_PORT') or 28015
PROJECT_DB = 'test'
PROJECT_TABLE = 'thinktor'
