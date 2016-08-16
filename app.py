import os, time
from datetime import datetime, date
import pytz
from tornado import websocket, web, ioloop, gen
import simplejson as json
# the Metro Network won't allow the process to contact Sentry, ugh
# from raven.contrib.tornado import AsyncSentryClient, SentryMixin
# private variables
from conf import cookie_secret, sentry_key, PORT, ADDRESS

# create logger
import logging
logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create log formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)
# logfile
hdlr = logging.FileHandler('logs/server.log')
hdlr.setLevel(logging.WARNING)
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

theclients = []
settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "cookie_secret": cookie_secret,
    # "login_url": "/login",
    # "xsrf_cookies": True,
}
# raven/sentry stuff


# this is for Raven
# class UncaughtExceptionHandler(web.RequestHandler):
#
#     def get(self):
#         1 / 0


class AsyncMessageHandler(web.RequestHandler):

    @web.asynchronous
    @gen.engine
    def get(self):
        self.write("You requested the main page")
        # yield gen.Task(
        #     # self.captureMessage, "Request for main page served"
        #     logger.info("Request for main page served")
        # )
        self.finish()


# class AsyncExceptionHandler(SentryMixin, web.RequestHandler):
class AsyncExceptionHandler(web.RequestHandler):

    @web.asynchronous
    @gen.engine
    def get(self):
        try:
            raise ValueError()
        except Exception as e:
            warningmsg = "%s | %s" %(e.message, e.args)
            logger.info(warningmsg)
            # response = yield gen.Task(
            #     self.captureException, exc_info=True
            # )
        self.finish()


# class IndexHandler(SentryMixin, web.RequestHandler):
class IndexHandler(web.RequestHandler):
    # SUPPORTED_METHODS = ("CONNECT", "GET", "HEAD", "POST", "DELETE", "PATCH", "PUT", "OPTIONS")
    SUPPORTED_METHODS = ("CONNECT", "GET", "HEAD", "OPTIONS")

    def head(self):
        """ Satisfy the Viewsonic browser that this url exists"""
        self.finish()

    def get(self):
        # self.captureMessage("Request for main page served")
        # logging
        logger.info("Request for main page served")
        self.render("index.html")


class SocketHandler(websocket.WebSocketHandler):

    def check_origin(self, origin):
        logger.info("check_origin: " +repr(origin))
        return True

    def open(self):
        if self not in theclients:
            logger.info("opened client: " +repr(self.get_status()))
            theclients.append(self)

    def on_close(self):
        if self in theclients:
            logger.info("closed client: " +repr(self.get_status()))
            theclients.remove(self)

    def on_message(self, message):
        logger.info("message received: " +repr(message))


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

                # logging
                logger.debug("------------" + item['res_general_desc'])
                logger.debug(item['room_name'])
                logger.debug(item['displaytime'])
                # logger.info(e.message, e.args)
                # logger.warn(e.message, e.args)
                # logger.error(e.message, e.args)
                # logger.critical(e.message, e.args)

                d = {}
                title = "title_%s" % i
                room = "room_%s" % i
                t = "time_%s" % i
                room_floor = "%s %s" %(item['room_name'], item['room_floor'])
                d = {title: item['res_general_desc'],
                     room: room_floor,
                     t: item['displaytime'],
                     }
                mlist.append(d)
            except Exception as e:
                warningmsg = "%s | %s" %(e.message, e.args)
                # logging
                # logger.debug(warningmsg)
                # logger.info(warningmsg)
                logger.warn(warningmsg)
                # logger.error(warningmsg)
                # logger.critical(warningmsg)
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

# app.sentry_client = AsyncSentryClient(
#     sentry_key
# )


# standlone server
if __name__ == '__main__':
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create log formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    logger.info("Tornado sign server server starting...")

    # 3. Make Tornado app listen on port
    app.listen(port=PORT, address=ADDRESS)

    # 4. Start IOLoop
    ioloop.IOLoop.instance().start()
