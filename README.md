
# Metro Signage Server
#### July 2016 | Douglas Goodwin

There are three parts to this application:

1. Python XML parser and emitter
2. JSON API
3. Websocket server

![overview](https://www.evernote.com/l/ADNCiwiMsOxEXIcAEwLsMAhkvxAhaTB4l-wB/image.png)

Part 1 GETs the XML, cleans it and POSTs the resulting JSON to part 2. Part 3 pushes content out to the clients over websockets. Note that parts 2 and 3 are combined into a single Tornado server.

## Get ready

```
virtualenv .
pip install -r requirements.txt

# set up your secret variables
cp mysettings.py.SAMPLE mysettings.py

# edit!
```

## Now run can the Tornado server

```
python app.py

# defaults to 127.0.0.1:8888 -- this may not be what you want!
```

## open a new terminal window and send some test events


```
python test.py
```

## See your results: [http://127.0.0.1:8888](http://127.0.0.1:8888)

## Voilà!

![screenshot](https://www.evernote.com/l/ADMi_5KFdtZDbJN39a-DIhkeCmPOyMAJyD8B/image.png)
