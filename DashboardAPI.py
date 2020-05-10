import os
import codecs
import json
import datetime

import flask
import werkzeug.exceptions
from google.cloud import datastore

import DataStore.DivcoDataStore as DivcoDataStore
import AuthModule
from Toolbox import jsonResponse

DSC = datastore.Client()

# def getProjectMetaTF(projectMetaItem):
#     dataItem = {}

    

#     return dataItem

class DashboardAPI:
    def __init__(self, app):
        app.add_url_rule('/papi/getProjectList', 'getProjectList', self.getProjectList)
        app.add_url_rule('/papi/createNewProject', 'createNewProject', self.createNewProject, methods=['POST'])
        app.add_url_rule('/papi/deleteProject', 'deleteProject', self.deleteProject, methods=['POST'])

    def getProjectList(self):
        activeAuthToken = AuthModule.validateCookie()
        activeUserData = DivcoDataStore.getUserByLoginSession(activeAuthToken)

        projectList = self.getAllUserProject(activeUserData.key.id)

        return jsonResponse(projectList, activeAuthToken)

    def createNewProject(self):
        activeAuthToken = AuthModule.validateCookie()
        activeUserData = DivcoDataStore.getUserByLoginSession(activeAuthToken)

        rawData = flask.request.form

        name = rawData.get("name")

        pID = DivcoDataStore.createNewProject(activeUserData.key.id, name)

        return jsonResponse({
            "msg" : "projectCreated", 
            "debug" : pID
        }, activeAuthToken)

    def deleteProject(self):
        activeAuthToken = AuthModule.validateCookie()
        activeUserData = DivcoDataStore.getUserByLoginSession(activeAuthToken)

        rawData = flask.request.form
        projectID = int(rawData.get("projectID"))

        DivcoDataStore.clearProject(projectID)

        return jsonResponse({
            "msg" : "projectDeleted"
        }, activeAuthToken)


    def getAllUserProject(self, userID):
        activeQuery = DSC.query(kind='projectMeta')
        activeQuery.add_filter('ownerUserList', '=', userID)

        userProjectList = activeQuery.fetch(limit=100)

        resultList = []
        for item in userProjectList:
            itemPID = item["projectID"]

            newestItem = DivcoDataStore.getNewestEntryFromProjectHistory(itemPID)
            if newestItem != None:
                lastUpdate = str(datetime.datetime.fromtimestamp(newestItem["ts"] / 1000).strftime(r"%Y-%m-%d %H:%M:%S"))
            else:
                lastUpdate = ""

            exportItem = {}
            exportItem["projectID"] = itemPID
            exportItem["projectName"] = item["name"]
            exportItem["userRole"] = "Owner"
            exportItem["lastUpdated"] = lastUpdate
            exportItem["completion"] = ""

            resultList.append(exportItem)
        
        activeQuery = DSC.query(kind='projectMeta')
        activeQuery.add_filter('assoUserList', '=', userID)

        userProjectList = activeQuery.fetch(limit=100)

        for item in userProjectList:
            itemPID = item["projectID"]

            newestItem = DivcoDataStore.getNewestEntryFromProjectHistory(itemPID)
            if newestItem != None:
                lastUpdate = str(datetime.datetime.fromtimestamp(newestItem["ts"] / 1000).strftime(r"%Y-%m-%d %H:%M:%S"))
            else:
                lastUpdate = ""

            exportItem = {}
            exportItem["projectID"] = itemPID
            exportItem["projectName"] = item["name"]
            exportItem["userRole"] = "User"
            exportItem["lastUpdated"] = lastUpdate
            exportItem["completion"] = ""

            resultList.append(exportItem)

        return resultList