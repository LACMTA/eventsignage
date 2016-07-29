import re, urllib2, os, time, json
from random import randrange, choice
from datetime import datetime, timedelta
from collections import OrderedDict
import xml.etree.ElementTree as ET
import pytz
import xmltodict
import requests
from jinja2 import Template, Environment, FileSystemLoader

DEBUG = True
XML_URL = 'http://meetingplannerxml'
xmlfile = 'MeetingPlanner.xml'
timeout = 2 # seconds

# thenow = datetime.now(pytz.timezone("America/Los_Angeles"))
# TypeError: can't compare offset-naive and offset-aware datetimes
thenow = datetime.now()
todaydisplay = thenow.strftime("%B %d, %Y")

signurl = "http://127.0.0.1:8888/api"
local_tz = pytz.timezone('America/Los_Angeles') # use your local timezone name here
timefmt = "%m/%d/%Y %I:%M:%S %p"

# def utc_to_local(utc_dt):
#     local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
#     return local_tz.normalize(local_dt) # .normalize might be unnecessary

def modification_date(afile):
    t = os.path.getmtime(afile)
    return datetime.fromtimestamp(t)

def fetchfile(XML_URL,timeout,xmlfile):
    try:
        r = urllib2.urlopen(XML_URL, timeout=timeout)
        if r.getcode() == 200:
            with open(xmlfile, 'w') as f:
                # line belows downloads entire file to memory,
                # and dumps it to file afterwards
                f.write(r.read())
            f.close()
            msg = "Got it %s" %(xmlfile)
            print(msg)
    except:
        print("There was an urllib2.urlopen error")

    return xmlfile, modification_date(xmlfile)

def tidymeup(s):
    s = s.replace('\r', '')
    s = s.replace('\t', ' ')
    s = s.replace('\f', ' ')
    s = s.replace("\'", '')
    return s

def write_testXML(xmlfile):
    reservations = []
    # set the start and end times
    thenow = datetime.now()
    curhour = thenow.hour
    nowtup = (thenow.year,thenow.month,thenow.day,thenow.hour,thenow.minute,thenow.second,0,0,0)
    nowt = time.strftime(timefmt, nowtup)
    midnighttup = (thenow.year,thenow.month,thenow.day,23,59,59,0,0,0)
    lastupdate = modification_date(xmlfile)

    for i,e in enumerate( range(8) ):
        # set up each test event
        subjects = ["TAC","Gold Line","Red Line","Union Station","Cafeteria","Art","LAX","San Francisco",]
        activities = ["Construction","Improvements","Upgrade", "Closing","RFP","Procurement","Planning","RFP"]
        meetingtypes = ["Committee","Scoping","Planning","EOL", "Discussion","RFC","Proposal", "Gripes"]
        rooms = ["Henry Huntington","Union Station","Board Room","Palos Verdes",
                 "East LA","Design Studio","Sierra Madre"]

        thetitle = "TEST! %s %s %s" %(choice(subjects),choice(activities),choice(meetingtypes))
        randhour = randrange(curhour,21)
        startmins = choice([0,15,30,45])
        rduration = choice([1,2])
        starttimetup = (thenow.year,thenow.month,thenow.day,randhour,startmins,0,0,0,0)
        endtimetup = (thenow.year,thenow.month,thenow.day,(randhour+rduration),startmins,0,0,0,0)
        start_dt = time.strftime(timefmt, starttimetup)
        end_dt = time.strftime(timefmt, endtimetup)

        # timestamps
        now_ts = time.mktime(nowtup)
        midnight_ts = time.mktime(midnighttup)
        start_ts = time.mktime(starttimetup)
        end_ts = time.mktime(endtimetup)

        reservation = {
            'order':i,
            'user_id':'71566',
            'res_id':randrange(11111,99999),
            'room_id':randrange(111,999),
            'start_dt':start_dt,
            'end_dt':end_dt,
            'room_name':choice(rooms),
            'general_desc':thetitle,
            'activity_cd':'000',
            'code_table_item_cd':'000',
            }
        # Append the meeting "current" if the end time is today between now and 11:59pm)
        if ( now_ts < end_ts < midnight_ts ):
            reservations.append(reservation)
    env = Environment(loader=FileSystemLoader('template'))
    template = env.get_template('base.xml')
    output_from_parsed_template = template.render(todaydisplay=todaydisplay,
                                              reservations=reservations,
                                             lastupdate=lastupdate)

    with open(xmlfile, "w") as fh:
        fh.write(output_from_parsed_template)
    fh.close()

    return xmlfile, modification_date(xmlfile)

def gimme_json(xmlfile,todaydisplay,lastupdate):
    thenow = datetime.now()
    updatestr = lastupdate.strftime("%B %d, %Y %I:%M %p")
    with open(xmlfile) as fd:
        doc = xmltodict.parse( tidymeup(fd.read()) )

    reservations_dict = doc[u'DocumentElement'][u'Reservation']
    reslist = []

    # get rid of duplicates
    for i,r in enumerate(reservations_dict):
        if r not in reslist:
            reslist.append(r)

    # sort and add order id
    sorted(reslist, key=lambda k: k['room_res_start_dt'])
    for i,r in enumerate(reslist):
        r['order']=i

    # top off the list with empty data
    empties = ( 8-len(reslist) )
    for i,e in enumerate( range(empties),100 ):
        r=OrderedDict([(u'order', i), (u'user_id', None), (u'res_id', u''), (u'room_id', u''), (u'Expr1', None), (u'Expr2', u''), (u'Expr3', None), (u'room_res_start_dt', u''), (u'room_res_end_dt', u''), (u'room_name', u''), (u'res_general_desc', u''), (u'res_activity_cd', None), (u'code_table_item_cd', None)])
        reslist.append(r)

    respackage = {'todaydisplay':todaydisplay,'current':[],'inprocess':[],'lastupdate':updatestr}
    for er in reslist:
        try:
            end_dt   = datetime.strptime(er['room_res_end_dt'], timefmt)
            current = (thenow < end_dt)
            if current:
                respackage['current'].append(er)
        except:
            # maybe no date was set?
            pass

        respackage['inprocess'].append(er)

    return json.dumps(respackage)




while True:
    if DEBUG:
        xmlfile,lastupdate = write_testXML(xmlfile)
        # DEBUG = False
    else:
        xmlfile,lastupdate = fetchfile(XML_URL,timeout,xmlfile)
        # DEBUG = True

    goj = gimme_json(xmlfile,todaydisplay,lastupdate)
    print(goj)
    r = requests.post( signurl, json=goj )
    time.sleep(15)  # Delay for 1 minute (60 seconds)
