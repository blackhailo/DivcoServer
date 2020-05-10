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

    divcoTileData = DivcoDataStore.getTileDataTree(projectID, tileID, 100)

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
    
    result = DivcoDataStore.addUserToProject(pID, email, rights)
    
    response = {}
    response["result"] = result

    return jsonResponse(response, authToken)

@app.route('/papi/export/<int:pID>')
def exportProject(pID):
    authToken = AuthModule.validateCookie()

    projectHistoryList = DivcoDataStore.getCompleteProjectHistory(pID)
    
    output = io.StringIO()

    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerows(projectHistoryList)

    data = output.getvalue()

    return csvResponse("test.csv", data, authToken)

@app.route('/papi/import/<int:pID>', methods=['POST'])
def importProject(pID):
    authToken = AuthModule.validateCookie()

    rawData = flask.request.form
    projectHistory = rawData.get("projectHistory")

    reader = csv.reader(io.StringIO(projectHistory))
    next(reader)
    for row in reader:
        entryType = row[1]
        entryArgs = row[2]

        DivcoDataStore.addToProjectHistory(pID, entryType, entryArgs)

    response = {}
    response["debug"] = projectHistory
    
    return jsonResponse(response)

@app.route('/papi/hack')
def hackspace():
    ## DO ONCE FOR SERVER SETUP
    # DivcoDataStore.initDivco()
    
    
    # CREATE NEW PROJECT
    

    # CLEAR AND RESET PROJECT
    DivcoDataStore.initDivco()


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

@app.route('/papi/test')
def testEndpoint():
    email = "test@wathever.com"
    name = "HailoTest"
    password = "ged"

    DivcoDataStore.createNewUser(name, email, password)

    response = {}
    
    return jsonResponse(response)


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
