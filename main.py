import os
import codecs
import json
import datetime

import io
import csv

import flask
import werkzeug.exceptions

from google.cloud import datastore
DSC = datastore.Client()

import DataStore.DivcoDataStore as DivcoDataStore
import DashboardAPI
import UserAPI

import AuthModule

from Toolbox import jsonResponse, csvResponse

app = flask.Flask(__name__)

UserAPI.UserAPI(app)
DashboardAPI.DashboardAPI(app)

@app.route('/')
@app.route('/dashboard')
@app.route('/tf_v2/<int:pID>/<int:tID>')
@app.route('/tf/<int:pID>/<int:tID>')
def reactClientHandler(pID = None, tID = None):
    print(flask.request.path)

    rawHtmlFile = codecs.open(r"static/index.html", encoding="utf-8")
    rawHtml = rawHtmlFile.read()
    rawHtmlFile.close()

    response = flask.Response(rawHtml)

    return response

@app.route('/papi/getTileData')
def getData():
    authToken = AuthModule.validateCookie()

    projectID = int(flask.request.args.get('projectID', ''))
    tileID = int(flask.request.args.get('tileID', ''))

    currentRoot = DivcoDataStore.getTileDataNode(projectID, tileID)
    divcoTileData = DivcoDataStore.getTileDataTree(projectID, tileID, currentRoot["stepCounter"] + 4)

    currentNode = DivcoDataStore.getTileDataNode(projectID, tileID)
    parentPath = currentNode["parentPath"]

    for pathTileID in parentPath:
        if pathTileID != tileID:
            pathNode = DivcoDataStore.getTileDataNode(projectID, pathTileID)
            divcoTileData.append(DivcoDataStore.getTransFormat(pathNode))

    response = {}
    response["crumbPath"] = parentPath
    response["data"] = divcoTileData

    return jsonResponse(response, authToken)


@app.route('/papi/reorderTile', methods=['POST'])
def reorderTile():
    authToken = AuthModule.validateCookie()
    rawData = flask.request.form

    projectID = int(rawData.get("projectID"))
    updateJsonString = rawData.get("tileData")
    
    entryType = "reorderTile"
    returnMessage = DivcoDataStore.addToProjectHistory(projectID, entryType, updateJsonString)

    response = {}
    response["result"] = returnMessage

    return jsonResponse(response, authToken)

@app.route('/papi/updateTile', methods=['POST'])
def updateTile():
    authToken = AuthModule.validateCookie()
    rawData = flask.request.form
    
    projectID = int(rawData.get("projectID"))
    updateJsonString = rawData.get("tileData")
    
    entryType = "updateTile"
    returnMessage = DivcoDataStore.addToProjectHistory(projectID, entryType, updateJsonString)

    response = {}
    response["result"] = returnMessage["status"]

    return jsonResponse(response, authToken)

@app.route('/papi/createTile', methods=['POST'])
def createTile():
    authToken = AuthModule.validateCookie()
    rawData = flask.request.form
    
    projectID = int(rawData.get("projectID"))
    updateJsonString = rawData.get("tileData")
    
    entryType = "createTile"
    returnMessage = DivcoDataStore.addToProjectHistory(projectID, entryType, updateJsonString)

    transTileChange = map(lambda node: DivcoDataStore.getTransFormat(node), returnMessage["tileChange"])

    response = {}
    response["result"] = returnMessage["status"]
    response["dataChange"] = list(transTileChange)

    return jsonResponse(response, authToken)

@app.route('/papi/deleteTile', methods=['POST'])
def deleteTile():
    authToken = AuthModule.validateCookie()
    rawData = flask.request.form
    
    projectID = int(rawData.get("projectID"))
    updateJsonString = rawData.get("tileData")
    
    entryType = "deleteTile"
    returnMessage = DivcoDataStore.addToProjectHistory(projectID, entryType, updateJsonString)

    response = {}
    response["result"] = returnMessage["status"]

    return jsonResponse(response, authToken)

@app.route('/papi/getProjectUserList/<int:pID>')
def getProjectUserList(pID):
    authToken = AuthModule.validateCookie()

    userList = DivcoDataStore.getProjectUserList(pID)
    
    response = {}
    response["data"] = userList

    return jsonResponse(response, authToken)

@app.route('/papi/addUserToProject/<int:pID>', methods=['POST'])
def addUserToProject(pID):
    authToken = AuthModule.validateCookie()
    rawData = flask.request.form
    
    email = rawData.get("email")
    rights = rawData.get("rights")
    
    response = {}
    try:
        result = DivcoDataStore.addUserToProject(pID, email, rights)
        response["result"] = result
    except ValueError as err:
        response["errorMsg"] = str(err)
    
    return jsonResponse(response, authToken)

@app.route('/papi/removeUserFromProject/<int:pID>', methods=['POST'])
def removeUserFromProject(pID):
    authToken = AuthModule.validateCookie()
    rawData = flask.request.form
    
    email = rawData.get("email")
    
    response = {}
    try:
        result = DivcoDataStore.removeUserFromProject(pID, email)
        response["result"] = result
    except ValueError as err:
        response["errorMsg"] = str(err)
    
    return jsonResponse(response, authToken)


@app.route('/papi/exportLegacyProject/<int:pID>')
def exportLegacyProject(pID):
    authToken = AuthModule.validateCookie()

    projectHistoryList = DivcoDataStore.getLegacyProjectHistory(pID)
    
    output = io.StringIO()

    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerows(projectHistoryList)

    data = output.getvalue()

    return csvResponse("p" + str(pID) + ".csv", data, authToken)


@app.route('/papi/importLegacy/<int:pID>', methods=['POST'])
def importLegacy(pID):
    authToken = AuthModule.validateCookie()

    DivcoDataStore.clearProject(pID)
    activeUserData = DivcoDataStore.getUserByLoginSession(authToken)
    DivcoDataStore.createNewProject(activeUserData.key.id, "Stub", pID)
    
    rawData = flask.request.form
    projectHistory = rawData.get("projectHistory")
    # projectMeta
    # createProjectMeta
    highestTileID = 0
    reader = csv.reader(io.StringIO(projectHistory))
    next(reader) #skip Header
    for row in reader:
        entryDate = row[0]
        entryType = row[1]
        entryArgs = row[2]

        if entryType == "reorderTiles":
            newEntryArgs = {}

            updateTileSet = []
            entryJson = json.loads(entryArgs)
            for key, value in entryJson.items():
                tileID = int(key)
                order = value
                updateTileSet.append([tileID, order])

            newEntryArgs["updateTileSet"] = updateTileSet
            DivcoDataStore.addToProjectHistory(pID, "reorderTile", json.dumps(newEntryArgs))
            print(pID, entryDate, "reorderTile", json.dumps(newEntryArgs))
        elif entryType == "setStatus":
            newEntryArgs = {}
            entryJson = json.loads(entryArgs)
            status = entryJson.get("status")
            if status == 2:
                status = 3
            elif status == 3:
                status = 2

            # for tileID in 
            newEntryArgs["tileIDList"] = entryJson.get("nodeIDList")
            newEntryArgs["status"] = status

            DivcoDataStore.addToProjectHistory(pID, "updateTile", json.dumps(newEntryArgs))
            print(pID, entryDate, "updateTile", json.dumps(newEntryArgs))
        elif entryType == "insertTile":
            newEntryArgs = {}
            entryJson = json.loads(entryArgs)
            # "{""status"":0,""ordering"":4,""forcedStatus"":false,""label"":""134"",""parent_path"":[1,4],""id"":4}"
            # "{""label"": ""abc"", ""parentID"": 1, ""tileID"": 4}"

            tileID = entryJson.get("id")
            newEntryArgs["tileID"] = tileID
            newEntryArgs["label"] = entryJson.get("label")

            parentPath = entryJson.get("parent_path")
            if len(parentPath) > 1:
                newEntryArgs["parentID"] = parentPath[-2]

            highestTileID = max(highestTileID, tileID)
            DivcoDataStore.addToProjectHistory(pID, "createTile", json.dumps(newEntryArgs))
            print(pID, entryDate, "createTile", json.dumps(newEntryArgs))
        elif entryType == "removeTile":
            newEntryArgs = {}
            entryJson = json.loads(entryArgs)
            # "removeTile","{""removedTileIDList"":[3,2]}"
            # "deleteTile","{""tileID"": 4}"

            newEntryArgs["tileIDList"] = list(set(entryJson.get("removedTileIDList")))
            DivcoDataStore.addToProjectHistory(pID, "deleteTile", json.dumps(newEntryArgs))
            print(pID, entryDate, "deleteTile", json.dumps(newEntryArgs))
        elif entryType == "modify":
            entryJson = json.loads(entryArgs)

            nodeIDList = entryJson.get("nodeIDList")
            nodeLabel = entryJson.get("label")
            parentPath = entryJson.get("parentPath")
            if parentPath != None:
                newParentID = parentPath[-2]
            else:
                newParentID = None
                
            # "modify","{""nodeIDList"":[4],""label"":""Kompetance s\u00e6tninger""}"
            # "updateTile","{""tileID"": 3, ""label"": ""Kompetance s\u00e6tninger nogeet""}"
            # 1565335615,"modify","{""nodeIDList"":[15],""parentPath"":[1,17,2,15]}"

            for tileID in nodeIDList:
                newEntryArgs = {}
                newEntryArgs["tileIDList"] = [tileID]

                if nodeLabel != None:
                    newEntryArgs["label"] = nodeLabel
                if newParentID != None:
                    newEntryArgs["parentID"] = newParentID
                
                DivcoDataStore.addToProjectHistory(pID, "updateTile", json.dumps(newEntryArgs))
                print(pID, entryDate, "updateTile", json.dumps(newEntryArgs))
                
        else:
            print("not implemented", entryType)
    
    # set TILE COUNT
    with DSC.transaction():
        projectMetaItem = DSC.get(DSC.key('projectMeta', pID))
        projectMetaItem.update({
            'tileCounter': highestTileID + 1
        })

        DSC.put(projectMetaItem)

    response = {}
    response["debug"] = projectHistory
    
    return jsonResponse(response)

@app.route('/papi/export/<int:pID>')
def exportProject(pID):
    authToken = AuthModule.validateCookie()

    projectHistoryList = DivcoDataStore.getCompleteProjectHistory(pID)
    
    output = io.StringIO()

    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerows(projectHistoryList)

    data = output.getvalue()

    return csvResponse("p" + str(pID) + ".csv", data, authToken)

@app.route('/papi/import/<int:pID>', methods=['POST'])
def importProject(pID):
    authToken = AuthModule.validateCookie()

    DivcoDataStore.clearProject(pID)
    activeUserData = DivcoDataStore.getUserByLoginSession(authToken)
    DivcoDataStore.createNewProject(activeUserData.key.id, "Stub", pID)

    rawData = flask.request.form
    projectHistory = rawData.get("projectHistory")

    maxUsedTileID = 0

    reader = csv.reader(io.StringIO(projectHistory))
    next(reader)
    for i, row in enumerate(reader):
        entryType = row[1]
        entryArgs = row[2]

        entryTileID = json.loads(entryArgs).get("tileID")
        if entryTileID:
            maxUsedTileID = max(entryTileID, maxUsedTileID)
        if i % 20 == 0:
            print(i, entryType, entryArgs)

        DivcoDataStore.addToProjectHistory(pID, entryType, entryArgs)

    with DSC.transaction():
        projectMetaItem = DSC.get(DSC.key('projectMeta', pID))
        projectMetaItem.update({
            'tileCounter': maxUsedTileID
        })

        DSC.put(projectMetaItem)

    response = {}
    response["debug"] = projectHistory
    
    return jsonResponse(response)

@app.route('/papi/hack')
def hackspace():
    pass
    ## DO ONCE FOR SERVER SETUP
    # DivcoDataStore.initDivco()
    
    
    # CREATE NEW PROJECT
    

    # CLEAR AND RESET PROJECT
    # DivcoDataStore.initDivco()


    # doReset = True
    # if doReset: ## TEST FLOW
    #     entryType = "createTile"
    #     rawEntryArgs = r'{"label":"tile_1","parentID":null}'
    #     DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

    #     entryType = "createTile"
    #     rawEntryArgs = r'{"label":"tile_2","parentID":1}'
    #     DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

    #     entryType = "updateTile"
    #     rawEntryArgs = r'{"tileID":1,"label":"TILE_1","status":3}'
    #     DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

    #     entryType = "deleteTile"
    #     rawEntryArgs = r'{"tileID":2}'
    #     DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

    #     entryType = "createTile"
    #     rawEntryArgs = r'{"label":"tile_3","parentID":1}'
    #     DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

    #     entryType = "createTile"
    #     rawEntryArgs = r'{"label":"tile_4","parentID":1}'
    #     DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

    #     entryType = "createTile"
    #     rawEntryArgs = r'{"label":"tile_5","parentID":1}'
    #     DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

    #     entryType = "reorderTile"
    #     rawEntryArgs = r'{"tileID":5,"order":1}'
    #     DivcoDataStore.addToProjectHistory(pID, entryType, rawEntryArgs)

    response = {}
    
    return jsonResponse(response)

# @app.route('/papi/test')
# def testEndpoint():
#     email = "test@wathever.com"
#     name = "HailoTest"
#     password = "ged"

#     DivcoDataStore.createNewUser(name, email, password)

#     response = {}
    
#     return jsonResponse(response)

@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
def page_not_found(error):
    return jsonResponse({
        "errorCode" : error.code,
        "errorMsg" : error.description
    }), error.code

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='localhost', port=51245, debug=True)
