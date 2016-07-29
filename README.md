
# Metro Signage Server
#### July 2016 | Douglas Goodwin

There are three parts to this application:

1. Python XML parser and emitter
2. JSON API
3. Websocket server

![overview](https://www.evernote.com/l/ADNCiwiMsOxEXIcAEwLsMAhkvxAhaTB4l-wB/image.png)

Part 1 GETs the XML, cleans it and POSTs the resulting JSON to part 2. Part 3 pushes content out to the clients over websockets. Note that parts 2 and 3 are combined into a single Tornado server.
