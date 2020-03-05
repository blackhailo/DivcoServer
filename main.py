#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sys
import webapp2
from webapp2_extras import sessions

import logging

import codecs
import os
import json


import DivcoDataStore


# import authInterface
# import tileLog
import time

sys.path.insert(1, './helpers')
import divCoUtil

from google.appengine.ext import ndb

if (os.getenv('SERVER_SOFTWARE') and os.getenv('SERVER_SOFTWARE').startswith('Google App Engine/')):
    ALLOWED_SCHEMES = ['https']
    DEV_FLAG = False
else:
    ALLOWED_SCHEMES = ['http']
    DEV_FLAG = True
    




# class TileHandler(BaseHandler):
#     def get(self, rawPID, rawTileID=None):
#         self.authI = authInterface.AuthInterface()
#         activeUser = self.authI.getUser()
        
#         if activeUser:
#             try:
#                 if rawTileID == None:
#                     tileID = "1"
#                 else:
#                     tileID = int(rawTileID)
                
#                 PID = int(rawPID)
#                 TPList = DSStructure.getTP_v2(PID, tileID)
                
#                 if TPList:            
#                     self.render("tileProjectViewer.html")
#                 else:
#                     responseDict = {"status": "failed",
#                                     "message": "Missing"}
                
#                     self.response.write(json.dumps(responseDict))
#             except TypeError:
#                 responseDict = {"status": "failed",
#                                 "message": "Invalid ID's supplied"}
                
#                 self.response.write(json.dumps(responseDict))
#         else:
#             responseDict = {"status": "failed",
#                             "message": unicode("no access")}
        
#             self.response.write(json.dumps(responseDict))

# class TileUpdateStreamHandler(BaseHandler):
#     def get(self, PID):
#         responseDict = {"message": "ged"}
        
#         self.response.write(json.dumps(responseDict))
        

# ## JS MODIFY DATA HANDLERS
# class UpdateHandler(BaseHandler):
#     def post(self, PID):
#         self.authI = authInterface.AuthInterface()
#         activeUser = self.authI.getUser()
        
#         if activeUser:
#             curTimeStamp = int(round(time.time()))
            
            # operation = cleanupParams(self.request.POST, "operation", str)
            # timeStamp = cleanupParams(self.request.POST, "ts", int)
            
#             data = cleanupParams(self.request.POST, "data", json.loads)
#             PID = int(PID)
            
#             if operation == "add":
#                 TSI = DSStructure.TileStorageInterface(PID, timeStamp, curTimeStamp)
#                 cLog = TSI.getOldLogEntries()
                
#                 TSI.insertTile(data)
                
#                 TSI.submitUpdates()
#                 TSI.submitLogEntries()
                
#                 cLog.extend(TSI.getNewLogEntries())
#                 TSI.clearLogEntries()
                
#                 responseDict = {"status": "success",
#                                 "ts": curTimeStamp,
#                                 "cLog": cLog}
#             elif operation == "remove":
#                 TSI = DSStructure.TileStorageInterface(PID, timeStamp, curTimeStamp)
#                 cLog = TSI.getOldLogEntries()
                
#                 TSI.removeTiles(data)
                
#                 TSI.submitLogEntries()
                
#                 cLog.extend(TSI.getNewLogEntries())
#                 TSI.clearLogEntries()
                
#                 responseDict = {"status": "success",
#                                 "ts": curTimeStamp,
#                                 "cLog": cLog}
            
#             elif operation == "setStatus":
#                 TSI = DSStructure.TileStorageInterface(PID, timeStamp, curTimeStamp)
#                 cLog = TSI.getOldLogEntries()
                
#                 TSI.setTileStatus(data)
                
#                 TSI.submitUpdates()
#                 TSI.submitLogEntries()
                
#                 cLog.extend(TSI.getNewLogEntries())
#                 TSI.clearLogEntries()
                
#                 responseDict = {"status": "success",
#                                 "ts": curTimeStamp,
#                                 "cLog": cLog}
                
#             elif operation == "modify":
#                 TSI = DSStructure.TileStorageInterface(PID, timeStamp, curTimeStamp)
#                 cLog = TSI.getOldLogEntries()
                
#                 TSI.modifyTiles(data)
                
#                 TSI.submitUpdates()
#                 TSI.submitLogEntries()
                
#                 cLog.extend(TSI.getNewLogEntries())
#                 TSI.clearLogEntries()
                
#                 responseDict = {"status": "success",
#                                 "ts": curTimeStamp,
#                                 "cLog": cLog}
#             elif operation == "reorder":
#                 TSI = DSStructure.TileStorageInterface(PID, timeStamp, curTimeStamp)
#                 cLog = TSI.getOldLogEntries()
                
#                 TSI.reorderTiles(data)
                
#                 TSI.submitUpdates()
#                 TSI.submitLogEntries()
                
#                 cLog.extend(TSI.getNewLogEntries())
#                 TSI.clearLogEntries()
                
#                 responseDict = {"status": "success",
#                                 "ts": curTimeStamp,
#                                 "cLog": cLog}
#             else:
#                 responseDict = {"status": "failed",
#                                 "message": unicode("invalid change type")}
#         else:
#             responseDict = {"status": "failed",
#                             "message": unicode("no access")}
        
#         self.response.write(json.dumps(responseDict))

# ## JS SERVE DATA HANDLERS
# class MetaVaultHandler(BaseHandler):
#     def get(self):
#         self.authI = authInterface.AuthInterface()
#         activeUser = self.authI.getUser()
        
#         if activeUser:
#             try:
#                 operation = cleanupParams(self.request.GET, "operation", unicode)
#                 PID = cleanupParams(self.request.GET, "PID", int)
                
#                 assoUserList = DSStructure.getAssoUserList(PID)
                
#                 responseDict = {"status": "success",
#                                 "data":assoUserList}
                
#             except ValueError as err:
#                 responseDict = {"status": "failed",
#                                 "message": unicode(err)}
#         else:
#             responseDict = {"status": "failed",
#                             "message": unicode("no access")}
        
#         self.response.write(json.dumps(responseDict))


# class VaultHandler(BaseHandler):
#     def get(self):
#         self.authI = authInterface.AuthInterface()
#         activeUser = self.authI.getUser()
        
#         if activeUser:
#             requestType = self.request.GET.get("requestType")
            
#             try:
#                 if requestType == "getTimeStamp":
#                     PID = cleanupParams(self.request.GET, "PID", int)
#                     timestamp = tileLog.getProjectTimeStamp(PID)
                    
#                     responseDict = {"status": "success",
#                                     "data": timestamp}
#                 elif requestType == "getTileData":
#                     PID = cleanupParams(self.request.GET, "PID", int)
#                     parentTileID = cleanupParams(self.request.GET, "parentTileID", int)
                    
#                     TPList = DSStructure.getTP_v2(PID, parentTileID)

#                     responseDict = {"status": "success",
#                                     "data": TPList}
#                 elif requestType ==  "getTileCrumbData":
#                     PID = cleanupParams(self.request.GET, "PID", int)
#                     parentTileID = cleanupParams(self.request.GET, "parentTileID", int)
                    
#                     parentTile = DSStructure.resolveTiles(PID, [parentTileID])[0]
#                     breadCrumbData = DSStructure.resolveTiles(PID, parentTile.get("parent_path"))
                    
#                     responseDict = {"status": "success",
#                                     "data": breadCrumbData}
#                 elif requestType == "getUserState":
#                     userID = activeUser.get("user_id")
                    
#                     PID = cleanupParams(self.request.GET, "PID", int)
#                     userStateDict = DSStructure.getUserStateDict(PID, userID)
                    
#                     responseDict = {"status": "success",
#                                     "data": userStateDict}
#                 elif requestType == "getTPBase":
#                     userID = activeUser.get("user_id")
                    
#                     PID = cleanupParams(self.request.GET, "PID", int)
#                     parentTileID = cleanupParams(self.request.GET, "parentTileID", int)
                    
#                     parentTile = DSStructure.resolveTiles(PID, [parentTileID])[0]
#                     parentPath = parentTile.get("parent_path")
                    
#                     userStateDict = DSStructure.getUserStateDict(PID, userID)
#                     pinList = userStateDict.get("projectPins")
                    
#                     missingTiles = []
                    
#                     TPList = DSStructure.getTP_v2(PID, parentTileID)
#                     TPTileData = {}
#                     for item in TPList:
#                         TPTileData[item.get("id")] = item
                    
#                     for pinID in pinList:
#                         tileData = TPTileData.get(pinID)
#                         if tileData == None:
#                             TPList = DSStructure.getTP_v2(PID, pinID)
#                             for item in TPList:
#                                 TPTileData[item.get("id")] = item
                            
#                             tileData = TPTileData.get(pinID)
                            
#                         for tileID in tileData.get("parent_path", []):
#                             tileParentData = TPTileData.get(tileID)
#                             if tileParentData == None:
#                                 missingTiles.append(tileID)
                    
#                     for tileID in parentPath:
#                         tileData = TPTileData.get(tileID)
#                         if tileData == None:
#                             missingTiles.append(tileID)
                    
#                     missingDataList = DSStructure.resolveTiles(PID, missingTiles)
#                     for item in missingDataList:
#                         TPTileData[item.get("id")] = item
                    
#                     responseDict = {"status": "success",
#                                     "timeStamp": tileLog.getProjectTimeStamp(PID),
#                                     "TPTileData": TPTileData,
#                                     "userStateDict": userStateDict}
#                 else:
#                     responseDict = {"status": "failed",
#                                     "message": unicode("invalid request type")}
#             except ValueError as err:
#                 responseDict = {"status": "failed",
#                                 "message": unicode(err)}
#         else:
#             responseDict = {"status": "failed",
#                             "message": unicode("no access")}
        
#         self.response.write(json.dumps(responseDict))

# class UserStateHandler(BaseHandler):
#     def post(self):
#         self.authI = authInterface.AuthInterface()
#         activeUser = self.authI.getUser()
        
#         if activeUser:
#             operation = cleanupParams(self.request.POST, "operation", unicode)
            
#             if operation == "infoBoxChange":
#                 data = cleanupParams(self.request.POST, "data", json.loads)
                
#                 userID = activeUser.get("user_id")
#                 userState = DSStructure.getUserState(userID)
                
#                 userState.infoBox = json.dumps(data)
#                 userState.put()
                
#                 responseDict = {"status": "success",
#                                 "message": unicode(userID)}
#             elif operation == "setPinnedTiles":
#                 data = cleanupParams(self.request.POST, "data", json.loads)
                
#                 PID = data.get("PID")
#                 pinnedToggleTileList = data.get("pinnedToggleTileList")
                
#                 userID = activeUser.get("user_id")
#                 userState = DSStructure.getUserState(userID)
                
#                 projectPinDict = json.loads(userState.projectPinDict)
#                 projectPinDict[str(PID)] = pinnedToggleTileList
#                 userState.projectPinDict = json.dumps(projectPinDict)
#                 userState.put()
                
#                 responseDict = {"status": "success",
#                                 "message": unicode(userID)}
#             else:
#                 responseDict = {"status": "failed",
#                                 "message": unicode("operation doesnt exist")}
                
#         else:
#             responseDict = {"status": "failed",
#                             "message": unicode("no access")}
            
#         self.response.write(json.dumps(responseDict))
            
# ##BROWSER FLOW HANDLERS
# class LoginHandler(BaseHandler):
#     def get(self):
#         self.authI = authInterface.AuthInterface()
#         activeUser = self.authI.getUser()
        
#         if activeUser:
#             return self.redirect("/console")
#         else:
#             self.render("login.html")
        
#     def post(self):
#         try:
#             email = cleanupParams(self.request.POST, "email", unicode)
#             password = cleanupParams(self.request.POST, "password", unicode)
            
#             self.authI = authInterface.AuthInterface()
#             self.authI.login(email, password)
            
#             responseDict = {"status": "success"}
#         except ValueError as err:
#             responseDict = {"status": "failed",
#                             "message": unicode(err)}
            
#         self.response.write(json.dumps(responseDict))

# class LogoutHandler(BaseHandler):
#     def get(self):
#         self.authI = authInterface.AuthInterface()
#         activeUser = self.authI.getUser()
        
#         if activeUser:
#             self.authI.logout()
#             return self.redirect("/")
#         else:
#             return self.redirect("/")
            

# class SignupHandler(BaseHandler):
#     def get(self):
#         self.render("signup.html")
        
#     def post(self):
#         try:
#             username = cleanupParams(self.request.POST, "username", unicode)
#             email = cleanupParams(self.request.POST, "email", unicode)
#             password = cleanupParams(self.request.POST, "password", unicode)
        
#             self.authI = authInterface.AuthInterface()
#             self.authI.create_user(username, email, password)
            
#             responseDict = {"status": "success"}
#         except ValueError as err:
#             responseDict = {"status": "failed",
#                             "message": unicode(err)}
        
#         self.response.write(json.dumps(responseDict))
        
# class UpdateDashboardHandler(BaseHandler):
#     def post(self):
#         try:
#             operation = cleanupParams(self.request.POST, "operation", unicode)
            
#             if operation == "newProject":
#                 timeStamp = int(round(time.time()))
#                 curTimeStamp = int(round(time.time()))
                
#                 projectName = cleanupParams(self.request.POST, "project_name", unicode)
#                 nextPID = DSStructure.getNextPID_v2()
                
#                 data = {"label": projectName}
                
#                 TSI = DSStructure.TileStorageInterface(nextPID, timeStamp, curTimeStamp)
#                 TSI.insertTile(data)
                
#                 TSI.submitUpdates()
#                 TSI.submitLogEntries()
                 
#                 self.authI = authInterface.AuthInterface()
#                 activeUser = self.authI.getUser()
                
#                 userAsso = DSStructure.UserAssociation()
#                 userAsso.email = activeUser.get("email_address")
#                 userAsso.PID = nextPID
#                 userAsso.permissionType = "admin"
                
#                 userAsso.put()
#                 responseDict = {"status": "done",
#                                 "message": unicode(operation)}
#             elif operation == "addUser":
#                 addEmail = cleanupParams(self.request.POST, "add_email", unicode)
#                 addRole = cleanupParams(self.request.POST, "add_role", unicode)
#                 PID = cleanupParams(self.request.POST, "PID", int)
                
#                 userAsso = DSStructure.UserAssociation()
#                 userAsso.email = addEmail
#                 userAsso.PID = PID
#                 userAsso.permissionType = addRole
                
#                 userAsso.put()
#                 responseDict = {"status": "done"}
#             elif operation == "removeProject":
#                 PID = cleanupParams(self.request.POST, "PID", int)
#                 DSStructure.removeProject(PID)
                
#                 responseDict = {"status": "done",
#                                 "message": "PID: " + unicode(PID) + "is hereby removed"}
#             else:
#                 responseDict = {"status": "failed",
#                                 "message": "invalid operation"}
        
#         except ValueError as err:
#             responseDict = {"status": "failed",
#                             "message": unicode(err)}
        
#         self.response.write(responseDict)
    
# class DashboardHandler(BaseHandler):
#     def get(self):
#         self.authI = authInterface.AuthInterface()
#         activeUser = self.authI.getUser()
        
#         context = {}
        
#         if activeUser:
#             context["userName"] = activeUser.get("name")
            
#             email = activeUser.get("email_address")
            
#             projectList = DSStructure.getAssoProjects(email)
#             context["projectList"] = projectList
            
#             self.render("dashboard.html", context)
#         else:
#             return self.redirect("/login")

# class MainHandler(BaseHandler):
#     def get(self):
#         self.authI = authInterface.AuthInterface()
#         activeUser = self.authI.getUser()
        
#         context = {}
#         if activeUser:
#             context["user"] = activeUser
        
#         self.render("main.html", context)

# ##ADMIN BACKEND HANDLERS
# class InitHandler(BaseHandler):
#     def get(self):
#         self.response.write("init")
        
#         # DSStructure.hack()
        
#         counter = DSStructure.Counter(id="0")
#         counter.nextPID = 0
#         counter.put()

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)       # dispatch the main handler
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()
    
    def webtemplate(self, template):
        rawHtmlFile = codecs.open(template, encoding="utf-8")
        rawHtml = rawHtmlFile.read()
        rawHtmlFile.close()

        return rawHtml
    
    def writeJsonResponse(self, responseDict):
        self.response.headers.add_header('Access-Control-Allow-Origin', 'http://localhost:3000')
        self.response.headers.add_header('Access-Control-Allow-Methods', "POST, GET")
        self.response.content_type = "application/json"
        self.response.write(json.dumps(responseDict, sort_keys=True))

    # def handle_exception(self, exception, debug):
    #     # Log the error.
    #     logging.exception(exception)

    #     # Set a custom message.
    #     self.response.write(exception.code)
    #     self.response.write("<br />")
    #     self.response.write("<br />")
    #     self.response.write(exception)

    #     # If the exception is a HTTPException, use its error code.
    #     # Otherwise use a generic 500 error code.
    #     if isinstance(exception, webapp2.HTTPException):
    #         self.response.set_status(exception.code)
    #     else:
    #         self.response.set_status(500)

class GetReactClientHandler(BaseHandler):
    def get(self, arg1=None, arg2=None):
        template = self.webtemplate("static\index.html")
        
        self.response.write(template)
        # gqlString = "SELECT * FROM TPStore_v2"
        # resultList, cursor, hasMore = DSStructure.runQuery(gqlString, 1000)
        # 
        # putList = []
        # for item in resultList:
        #     item.stepCounter = len(item.parentPath)
        #     
        #     if item.status == 0:
        #         item.forcedStatus = False
        #     else:
        #         item.forcedStatus = True
        #     
        #     putList.append(item)
        # 
        # ndb.put_multi(putList)

class HackDataHandler(BaseHandler):
    def get(self):
        DTDM = DivcoDataStore.DivcoTileDataManager(1)
        # DTDM.addToModiTile()
        DTDM.submitUpdates()

        self.writeJsonResponse({"oki" : "doki"})

class UpdateDataHandler(BaseHandler):
    def get(self):
        DTDM = DivcoDataStore.DivcoTileDataManager(1)

        # deltaTileDataState = {
        #     "tileID" : 1,
        #     "parent" : None,
        #     "status" : 0,
        #     "label" : "superTile"
        # }

        # DTDM.addToModiTile(deltaTileDataState)
        # DTDM.submitUpdates()

    def post(self):

        # operation = cleanupParams(self.request.POST, "operation", str)
        # timeStamp = cleanupParams(self.request.POST, "ts", int)
        
        tileID = None
        parent = 1
        status = 0
        label = "AB"

        deltaTileDataState = {
            "tileID" : tileID,
            "parent" : parent,
            "label" : label,
            "status" : status
        }
        
        DTDM = DivcoDataStore.DivcoTileDataManager(1)
        DTDM.updateTile(deltaTileDataState)
        DTDM.submitUpdates()

        response = {}
        response["status"] = "sucess"
        response["dataChange"] = [
            {"id" : tileID, 
            "parent" : parent, 
            "name" : label, 
            "status" : status}
        ]

        self.writeJsonResponse(response)

class GetDataHandler(BaseHandler):
    def get(self):
        try:
            projectID = divCoUtil.cleanupParams(self.request.GET, "projectID", int, True)
            tileID = divCoUtil.cleanupParams(self.request.GET, "tileID", int, True)
        
        
            divCoTileParentPath = []
            divCoTileDataStump = [
                ["1", None, "A", 3],
                ["2", "1", "B", 1],
                ["3", "1", "C", 0],
                ["6", "2", "F", 3],
                ["4", "3", "D", 2],
                ["5", "3", "E", 0],
                
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

            self.writeJsonResponse(response)
        except ValueError as cleanupErr:
            self.abort(400)

CONFIG = {
  'webapp2_extras.auth': {
    'user_model': 'DSStructure.User',
    'user_attributes': ['email_address', 'name']
  },
  'webapp2_extras.sessions': {
    'secret_key': '22fe0dc5426b9f86848073c2c6f7bb82dabcd24139603c73'
  }
}

app = webapp2.WSGIApplication([
    ##APP endpoints
    webapp2.Route('/', handler=GetReactClientHandler, schemes=ALLOWED_SCHEMES),
    webapp2.Route('/dashboard', handler=GetReactClientHandler, schemes=ALLOWED_SCHEMES),
    webapp2.Route('/tf/<:\w+>/<:\w+>', handler=GetReactClientHandler, schemes=ALLOWED_SCHEMES),

    ##DATA endpoints
    webapp2.Route('/papi/getTileData', handler=GetDataHandler, schemes=ALLOWED_SCHEMES),
    webapp2.Route('/papi/updateTileData', handler=UpdateDataHandler, schemes=ALLOWED_SCHEMES),

    webapp2.Route('/papi/hackSpace', handler=HackDataHandler, schemes=ALLOWED_SCHEMES),

    ##JS ENDPOINTS
    # webapp2.Route('/vault', handler=VaultHandler, schemes=ALLOWED_SCHEMES),
    # webapp2.Route('/updateUserState', handler=UserStateHandler, schemes=ALLOWED_SCHEMES),
    
    # webapp2.Route('/metaVault', handler=MetaVaultHandler, schemes=ALLOWED_SCHEMES),
    # webapp2.Route('/updateDashboard', handler=UpdateDashboardHandler, schemes=ALLOWED_SCHEMES),
    
    # webapp2.Route('/update/<:\w+>', handler=UpdateHandler, schemes=ALLOWED_SCHEMES),
    # ##TILEPLANNER MAIN VIEW
    # webapp2.Route('/TP/<:\w+>_<:\w+>', handler=TileHandler, schemes=ALLOWED_SCHEMES),
    # webapp2.Route('/TP/<:\w+>', handler=TileHandler, schemes=ALLOWED_SCHEMES),
    # webapp2.Route('/tileUpdateStream/<:\w+>', handler=TileUpdateStreamHandler, schemes=ALLOWED_SCHEMES),
    
    # ##STANDART ENDPOINTS
    # webapp2.Route('/login', handler=LoginHandler, schemes=ALLOWED_SCHEMES),
    # webapp2.Route('/logout', handler=LogoutHandler, schemes=ALLOWED_SCHEMES),
    # webapp2.Route('/signup', handler=SignupHandler, schemes=ALLOWED_SCHEMES),
    # webapp2.Route('/dashboard', handler=DashboardHandler, schemes=ALLOWED_SCHEMES),
    
    # ##HACKY ADMIN ENDPOINTS
    # webapp2.Route('/init', handler=InitHandler, schemes=ALLOWED_SCHEMES),
    # webapp2.Route('/projecthack', handler=HackHandler, schemes=ALLOWED_SCHEMES),
    # webapp2.Route('/reactApp', handler=HackHandler, schemes=ALLOWED_SCHEMES),
    
    # ############################
    # webapp2.Route('/', handler=MainHandler, schemes=ALLOWED_SCHEMES)
], debug=True, config=CONFIG)




