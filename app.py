import os, time
from datetime import datetime, date
import pytz
from tornado import websocket, web, ioloop, gen
import simplejson as json
from raven.contrib.tornado import AsyncSentryClient, SentryMixin
# private variables
from conf import cookie_secret, sentry_key, PORT

DEBUG = False
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
            sorted_meetings = sorted(js['current'], key=lambda k: k['ts'])
        except ValueError:
            raise tornado.httpserver._BadRequestException(
                "Invalid JSON structure."
            )

        # display today
        now = datetime.now()
        dayint = datetime.now().day
        if (4 <= dayint <= 20) or (24 <= dayint <= 30):
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][dayint % 10 - 1]
        today = "%s %s%s, %s" % (now.strftime(
            "%A %B"), dayint, suffix, datetime.now().year)

        mlist = []
        postme = True
        for i, item in enumerate(sorted_meetings[0:15]):
            try:
                if item['res_general_desc'] == None:
                    item['res_general_desc'] = "Untitled Meeting"
                if DEBUG:
                    print("------------" + item['res_general_desc'])
                    print(item['room_name'])
                    print(item['displaytime'])
                d = {}
                title = "title_%s" % i
                room = "room_%s" % i
                t = "time_%s" % i
                d = {title: item['res_general_desc'],
                     room: item['room_name'], t: item['displaytime']}
                mlist.append(d)
            except Exception as e:
                # print(print e.message, e.args)
                postme = False

        if (postme):
            for d in mlist:
                for k, v in d.items():
                    msg = {"id": k, "value": v}
                    for c in theclients:
                        c.write_message(msg)
            # now, the metadata
            for c in theclients:
                c.write_message(
                    {"id": "lastupdate", "value": "last update: " + js["lastupdate"]})
                c.write_message({"id": "display_today", "value": today})

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
    app.listen(port=PORT, address='0.0.0.0')

    # 4. Start IOLoop
    ioloop.IOLoop.instance().start()
