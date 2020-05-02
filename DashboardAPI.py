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

def getProjectMetaTF(projectMetaItem):
    dataItem = {}

    dataItem["projectID"] = projectMetaItem["projectID"]
    dataItem["projectName"] = projectMetaItem["name"]

    return dataItem

class DashboardAPI:
    def __init__(self, app):
        app.add_url_rule('/papi/getProjectList', 'getProjectList', self.getProjectList)

    def getProjectList(self):
        activeAuthToken = AuthModule.validateCookie()
        activeUserData = DivcoDataStore.getUserByLoginSession(activeAuthToken)

        projectList = self.getAllUserProject(activeUserData["name"])

        return jsonResponse(projectList, activeAuthToken)

    def getAllUserProject(self, userName):
        activeQuery = DSC.query(kind='projectMeta')
        activeQuery.add_filter('assoUserList', '=', userName)

        userProjectList = activeQuery.fetch(limit=100)

        resultList = []

        for item in userProjectList:
            exportItem = getProjectMetaTF(item)

            exportItem["userRole"] = ""
            exportItem["lastUpdated"] = ""
            exportItem["completion"] = ""

            resultList.append(exportItem)

        return resultList