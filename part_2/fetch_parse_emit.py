import re, os, time, json
from random import randrange, choice
from datetime import datetime, timedelta
from collections import OrderedDict
import xml.etree.ElementTree as ET
import pytz
import xmltodict
import requests
# from tzlocal import get_localzone -- use this if you're not sure about the local TZ
from jinja2 import Template, Environment, FileSystemLoader
# import rethinkdb as rdb

from conf import SIGNURL, XML_URL, TIMEOUT, LOCAL_TZ, XMLFILE
# rethinkdb settings
# from conf import RDB_HOST,RDB_PORT,PROJECT_DB,PROJECT_TABLE

# set up all the variables
DEBUG = False
# time
UTC_tz = pytz.timezone('UTC')
thenow = datetime.now(LOCAL_TZ)
thenow_utc = datetime.now(UTC_tz)
# offset-naive and offset-aware datetimes ?
# remove the timezone awareness, yuk!
naive_utc = thenow_utc.replace(tzinfo=None)
todaydisplay = thenow.strftime("%B %d, %Y")
timefmt = "%m/%d/%Y %I:%M:%S %p"

# Connect to the RethinkDB server
# RDB_HOST =  os.environ.get('RDB_HOST') or 'localhost'
# RDB_PORT = os.environ.get('RDB_PORT') or 28015
# RDB_DB = 'meetings'
#
# rdb_conn = rdb.connect(host=RDB_HOST, port=RDB_PORT, db=RDB_DB)

def parse_mptime(timestr="8/8/2016 1:00:00 PM", timefmt = "%m/%d/%Y %I:%M:%S %p"):
    # MP time is UTC
    timedict = {}
    timedict["original"] = timestr
    timedict["timefmt"] = timefmt
    timedict["LOCAL_TZ"] = pytz.timezone("America/Los_Angeles")
    LOCAL_TZ = pytz.timezone("America/Los_Angeles")
    utc_tz = pytz.timezone ("UTC")
    naive_time = datetime.strptime(timestr, timefmt)
    mptime = utc_tz.localize(naive_time)
    utc_time = utc_tz.localize(naive_time)
    timedict["timestamp"] = time.mktime(utc_time.timetuple())
    localtime = utc_time.astimezone(LOCAL_TZ)
    timedict["local"] = localtime
    timedict["displaytime"] = timedict['local'].strftime('%I:%M %p')
    timedict["displaydate"] = timedict['local'].strftime('%m/%d/%Y')
    timedict["json_date"] = localtime.isoformat()
    # is this time in the future?
    utcnow = utc_tz.localize(datetime.utcnow())
    timedict["isfuture"] = (utcnow <= utc_time)
    # is this today?
    localnow = LOCAL_TZ.localize(datetime.now())
    timedict["endstoday"] = (localnow.year,localnow.month,localnow.day) == (localtime.year,localtime.month,localtime.day)
    return timedict

def modification_date(afile):
    t = os.path.getmtime(afile)
    return datetime.fromtimestamp(t)

def fetchfile(XML_URL,TIMEOUT,XMLFILE):
    try:
        r = requests.get(XML_URL)
        if r.status_code == 200:
            with open(XMLFILE, 'w') as f:
                # line belows downloads entire file to memory,
                # and dumps it to file afterwards
                f.write(r.content)
            f.close()
            msg = "Got it %s" %(XMLFILE)
            print(msg)
    except Exception as e:
        print(e.message, e.args)

    return XMLFILE, modification_date(XMLFILE)

def tidymeup(s):
    s = s.replace('\r', '')
    s = s.replace('\t', ' ')
    s = s.replace('\f', ' ')
    s = s.replace("\'", '')
    return s

# def gimme_json(XMLFILE,todaydisplay,lastupdate,rdb):
def gimme_json(XMLFILE,todaydisplay,lastupdate):
    updatestr = lastupdate.strftime("%B %d, %Y %I:%M %p")
    with open(XMLFILE) as fd:
        doc = xmltodict.parse( tidymeup(fd.read()) )

    reservations_dict = doc[u'DocumentElement'][u'Reservation']
    reslist = []

    # get rid of duplicates
    for i,res in enumerate(reservations_dict):
        if res not in reslist:
            reslist.append(res)

    # sort and add order id
    sorted(reslist, key=lambda k: k['room_res_start_dt'])
    for i,res in enumerate(reslist):
        res['order']=i

    # top off the list with empty data
    empties = ( 16-len(reslist) )
    for i,e in enumerate( range(empties),100 ):
        r=OrderedDict([(u'order', i), (u'id', u''), (u'user_id', None), (u'res_id', u''), (u'room_id', u''), (u'Expr1', None), (u'Expr2', u''), (u'Expr3', None), (u'room_res_start_dt', u''), (u'room_res_end_dt', u''), (u'ts', u''), (u'displaytime', u''),(u'room_name', u''), (u'res_general_desc', u''), (u'res_activity_cd', None), (u'code_table_item_cd', None)])
        reslist.append(r)

    respackage = {'todaydisplay':todaydisplay,'current':[],'inprocess':[],'future':[],'lastupdate':updatestr}
    for er in reslist:
        er['id'] = er['res_id']
        st_dict = parse_mptime(er['room_res_start_dt'])
        et_dict = parse_mptime(er['room_res_end_dt'])
        if (et_dict['isfuture']):
            try:
                er['displaytime'] = "%s - %s" %(st_dict['displaytime'], et_dict['displaytime'])
                er['ts'] = st_dict['timestamp']
                if et_dict['endstoday']:
                    respackage['current'].append(er)
                    # add it to rethinkdb
                    # rdb.db("meetings").table("current").insert(er).run(rdb_conn)
            except Exception as e:
                # maybe no date was set?
                print(print e.message, e.args)
                pass

            respackage['inprocess'].append(er)

    return json.dumps(respackage)




while True:
    XMLFILE,lastupdate = fetchfile(XML_URL,TIMEOUT,XMLFILE)

    # goj = gimme_json(XMLFILE,todaydisplay,lastupdate,rdb)
    goj = gimme_json(XMLFILE,todaydisplay,lastupdate)
    # print(goj)
    r = requests.post( SIGNURL, json=goj )
    time.sleep(60)  # Delay for 1 minute (60 seconds)
