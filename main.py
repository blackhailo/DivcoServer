import os
import codecs
import json
import datetime

import flask
import werkzeug.exceptions

from google.cloud import datastore
DSC = datastore.Client()

import DataStore.DivcoDataStore as DivcoDataStore

def store_time(dt):
    # with client.transaction():
    entity = datastore.Entity(key=DSC.key('visit'))
    entity.update({
        'timestamp': dt
    })

    DSC.put(entity)

def fetch_times(limit):
    query = DSC.query(kind='visit')
    query.order = ['-timestamp']

    times = query.fetch(limit=limit)

    return times

def jsonResponse(responseDict):
    resp = flask.Response(json.dumps(responseDict, sort_keys=True), content_type="application/json")


    resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    resp.headers['Access-Control-Allow-Methods'] = 'POST,GET'
    resp.headers['Access-Control-Request-Headers'] = 'Content-Type'

    resp.headers['Vary'] = 'Origin'
    
    return resp

app = flask.Flask(__name__)

@app.route('/')
@app.route('/dashboard')
@app.route('/tf/<int:pID>/<int:tID>')
def reactClientHandler(pID = None, tID = None):
    # rawHtmlFile = codecs.open(r"static/index.html", encoding="utf-8")
    # rawHtml = rawHtmlFile.read()
    # rawHtmlFile.close()

    store_time(datetime.datetime.now())

    times = fetch_times(1000)

    output = ""
    stringTimes = map(lambda item: str(item['timestamp']), times)
    
    resp = flask.Response("<br />".join(stringTimes))
    # resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    # resp.headers['Access-Control-Allow-Methods'] = 'POST,GET'
    # resp.headers['Access-Control-Request-Headers'] = 'Content-Type'

    return resp

@app.route('/papi/getTileData')
def getData():
    projectID = int(flask.request.args.get('projectID', ''))
    tileID = int(flask.request.args.get('tileID', ''))

    divCoTileParentPath = []
    divCoTileDataStump = [
        ["1", None, "A", 3],
        ["2", "1", "B", 1],
        ["3", "1", "C", 0],
        ["6", "2", "F", 3],
        ["4", "3", "D", 2],
        ["5", "3", "E", 0]
    ]

    tableStump = {
        1 : {"id" : 1, "parent" : None, "pPath" : [1], "name" : "A", "status" : 3},
        2 : {"id" : 2, "parent" : 1, "pPath" : [1,2], "name" : "B", "status" : 1},
        3 : {"id" : 3, "parent" : 1, "pPath" : [1,3], "name" : "C", "status" : 0},
        4 : {"id" : 4, "parent" : 3, "pPath" : [1,3,4], "name" : "D", "status" : 2},
        5 : {"id" : 5, "parent" : 3, "pPath" : [1,3,5], "name" : "E", "status" : 0},
        6 : {"id" : 6, "parent" : 2, "pPath" : [1,2,6], "name" : "F", "status" : 3}
    }
    
    activeSet = set()
    topLevelPath = None
    divCoTileData = []
    for tileDataItem in tableStump.values():
        pPath = tileDataItem.pop("pPath")

        if tileID in pPath:
            divCoTileData.append(tileDataItem)
            activeSet.add(tileID)

            if tileDataItem["id"] == tileID:
                topLevelPath = pPath

    for cTID in topLevelPath:
        if not cTID in activeSet:
            divCoTileData.append(tableStump.get(cTID))

    response = {}
    response["parentPath"] = divCoTileParentPath
    response["TLT"] = topLevelPath
    response["data"] = divCoTileData

    return jsonResponse(response)

def getAllUserProject(userName):
    activeQuery = DSC.query(kind='projectMeta')
    activeQuery.add_filter('assoUserList', '=', userName)

    userProjectList = activeQuery.fetch(limit=100)

    return userProjectList

# class ProjectHistory(ndb.Model):
#     pid = ndb.IntegerProperty()
#     ts = ndb.DateTimeProperty(auto_now=True)
#     eventType = ndb.StringProperty()
#     eventData = ndb.TextProperty()

@app.route('/papi/hack')
def hackspace():
    # initDivco()
    # nextPID = incProjectCounter()


    pID = 3

    doReset = True
    if doReset: ## TEST FLOW
        DivcoDataStore.clearProject(pID)

        DivcoDataStore.createProjectMeta(pID)

        entryType = "createTile"
        rawEntryArgs = r'{"label":"tile_1","parentID":null}'
        DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

        entryType = "createTile"
        rawEntryArgs = r'{"label":"tile_2","parentID":1}'
        DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

        entryType = "updateTile"
        rawEntryArgs = r'{"tileID":1,"label":"TILE_1","status":3}'
        DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

        entryType = "deleteTile"
        rawEntryArgs = r'{"tileID":2}'
        DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

        entryType = "createTile"
        rawEntryArgs = r'{"label":"tile_3","parentID":1}'
        DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

        entryType = "createTile"
        rawEntryArgs = r'{"label":"tile_4","parentID":1}'
        DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

        entryType = "createTile"
        rawEntryArgs = r'{"label":"tile_5","parentID":1}'
        DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

        entryType = "reorderTile"
        rawEntryArgs = r'{"tileID":5,"order":1}'
        DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)



    
    response = {}
    
    
    # userProjectList = getAllUserProject("C")

    return jsonResponse(response)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
