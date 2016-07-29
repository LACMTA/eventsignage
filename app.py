import os
from datetime import datetime, date
import pytz
from tornado import websocket, web, ioloop, gen
import simplejson as json
from raven.contrib.tornado import AsyncSentryClient, SentryMixin
# private variables
from mysettings import cookie_secret, sentry_key

local_tz = pytz.timezone('America/Los_Angeles') # use your local timezone name here
theclients = []
settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": cookie_secret,
    # "login_url": "/login",
    # "xsrf_cookies": True,
}
# raven/sentry stuff


class UncaughtExceptionHandler(SentryMixin, web.RequestHandler):

    def get(self):
        1 / 0


class AsyncMessageHandler(SentryMixin, web.RequestHandler):

    @web.asynchronous
    @gen.engine
    def get(self):
        self.write("You requested the main page")
        yield gen.Task(
            self.captureMessage, "Request for main page served"
        )
        self.finish()


class AsyncExceptionHandler(SentryMixin, web.RequestHandler):

    @web.asynchronous
    @gen.engine
    def get(self):
        try:
            raise ValueError()
        except Exception as e:
            response = yield gen.Task(
                self.captureException, exc_info=True
            )
        self.finish()


class IndexHandler(SentryMixin, web.RequestHandler):
    # SUPPORTED_METHODS = ("CONNECT", "GET", "HEAD", "POST", "DELETE", "PATCH", "PUT", "OPTIONS")
    SUPPORTED_METHODS = ("CONNECT", "GET", "HEAD", "OPTIONS")

    def head(self):
        """ Satisfy the Viewsonic browser that this url exists"""
        self.finish()

    def get(self):
        self.captureMessage("Request for main page served")
        self.render("index.html")

# original method
class SocketHandler(websocket.WebSocketHandler):

    def check_origin(self, origin):
        return True

    def open(self):
        if self not in theclients:
            theclients.append(self)

    def on_close(self):
        if self in theclients:
            theclients.remove(self)

class ApiHandler(web.RequestHandler):

    def tidymeup(self, s):
        s = s.replace('\r', '')
        s = s.replace('\t', ' ')
        s = s.replace('\f', ' ')
        s = s.replace("\'", '')
        return s

    def utc_to_local(self,utc_dt):
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt) # .normalize might be unnecessary


    @web.asynchronous
    def get(self, *args):
        # curl "http://127.0.0.1:8888/api?id=9&value=Henry-Huntington"
        self.finish()
        id = self.get_argument("id")
        value = self.get_argument("value")
        data = {"id": id, "value": value}
        data = json.dumps(data)
        for c in theclients:
            c.write_message(data)

    @web.asynchronous
    def post(self):
        raw_data = self.request.body
        json_data = json.loads(raw_data)
        self.finish()

        try:
            js = json.loads(json_data)
            sorted_meetings = sorted(js['current'], key=lambda k: k['order'])
        except ValueError:
            raise tornado.httpserver._BadRequestException(
                "Invalid JSON structure."
            )

        mlist = []
        postme = True
        for i, item in enumerate(sorted_meetings):
            try:
                timefmt = "%m/%d/%Y %I:%M:%S %p"
                today = date.today()
                today_YMD = today.strftime("%Y_%m_%d")
                print("----- item['room_res_start_dt'] -------")
                print item['room_res_start_dt']
                start_utc = datetime.strptime(item['room_res_start_dt'], timefmt)
                end_utc   = datetime.strptime(item['room_res_end_dt'], timefmt)
                start_dt = self.utc_to_local(start_utc).strftime(timefmt)
                end_dt = self.utc_to_local(end_utc).strftime(timefmt)
                myend_YMD = datetime.strptime(end_dt, timefmt).strftime("%Y_%m_%d")
                if (today_YMD == myend_YMD):
                    d = {}
                    title = "title_%s" % i
                    room = "room_%s" % i
                    t = "time_%s" % i

                    tstr = "%s - %s" % (start_dt,end_dt)
                    d = {title: item['res_general_desc'],
                         room: item['room_name'], t: tstr}
                    mlist.append(d)

            except:
                postme = False

        if (postme):
            for d in mlist:
                for k, v in d.items():
                    msg = {"id": k, "value": v}
                    for c in theclients:
                        c.write_message(msg)
            # now, the metadata
            for c in theclients:
                c.write_message({"id": "lastupdate", "value": js["lastupdate"]})

# 2. Create Tornado application
app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/api', ApiHandler),
    (r'/(favicon.ico)', web.StaticFileHandler, {'path': '../'}),
    (r'/(rest_api_example.png)', web.StaticFileHandler, {'path': './'}),
], **settings)

app.sentry_client = AsyncSentryClient(
    sentry_key
)


# standlone server
if __name__ == '__main__':
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    # 3. Make Tornado app listen on port
    app.listen(port=8888, address='0.0.0.0')

    # 4. Start IOLoop
    ioloop.IOLoop.instance().start()
