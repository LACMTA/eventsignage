import os
import pytz

PORT=9999
SIGNURL="http://127.0.0.1:%s/api" %(PORT)
XML_URL = 'http://meetingplannerxml'
TIMEOUT = 2 # seconds
LOCAL_TZ = pytz.timezone('America/Los_Angeles') # use your local timezone name here
XMLFILE = 'MeetingPlanner.xml'

# rethinkdb settings
RDB_HOST =  os.environ.get('RDB_HOST') or 'localhost'
RDB_PORT = os.environ.get('RDB_PORT') or 28015
PROJECT_DB = 'test'
PROJECT_TABLE = 'thinktor'
