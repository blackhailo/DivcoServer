import flask
import codecs
import json
import werkzeug.exceptions

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
    rawHtmlFile = codecs.open(r"static/index.html", encoding="utf-8")
    rawHtml = rawHtmlFile.read()
    rawHtmlFile.close()

    resp = flask.Response(rawHtml)

    resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    resp.headers['Access-Control-Allow-Methods'] = 'POST,GET'
    resp.headers['Access-Control-Request-Headers'] = 'Content-Type'

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

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
