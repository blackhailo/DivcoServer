import datetime
import time
import json
import hashlib

from google.cloud import datastore
DSC = datastore.Client()

import Toolbox

### GLOBAL
def initDivco():
    pCounter = datastore.Entity(key=DSC.key('counter', "pCounter"))
    pCounter.update({
        'count': 0
    })

    DSC.put(pCounter)

def incProjectCounter():
    currentCount = None
    with DSC.transaction():
        pCounter = DSC.get(DSC.key('counter', "pCounter"))
        currentCount = pCounter["count"]

        pCounter.update({
            'count': currentCount + 1
        })

        DSC.put(pCounter)

    return currentCount + 1

### PROJECT
def createProjectMeta(projectID):
    projectMetaItem = datastore.Entity(key=DSC.key('projectMeta', projectID))

    projectMetaItem.update({
        'projectID': projectID,
        'name': "Test",
        'assoUserList': ["A", "C", "D"],
        'tileCounter' : 0
    })

    DSC.put(projectMetaItem)

def clearProject(projectID):
    projectMetaKey = DSC.key('projectMeta', projectID)

    tileDataQuery = DSC.query(kind='projectTileData')
    tileDataQuery.add_filter('projectID', '=', projectID)
    tileDataQuery.keys_only()

    queryHistory = DSC.query(kind='projectHistory')
    queryHistory.add_filter('projectID', '=', projectID)
    queryHistory.keys_only()
    
    batch = DSC.batch()
    with batch:
        batch.delete(projectMetaKey)
        for item in tileDataQuery.fetch():
            batch.delete(item.key)
        for item in queryHistory.fetch():
            batch.delete(item.key)

def incTileCounter(pIDstring):
    currentCount = None

    with DSC.transaction():
        projectMetaItem = DSC.get(DSC.key('projectMeta', pIDstring))
        currentCount = projectMetaItem["tileCounter"]

        projectMetaItem.update({
            'tileCounter': currentCount + 1
        })

        DSC.put(projectMetaItem)

    return currentCount + 1

# MAIN DATA-STRUCTURES
def addToProjectHistory(pID, entryType, rawEntryArgs):
    projectHistoryItem = datastore.Entity(key=DSC.key('projectHistory'), exclude_from_indexes=["entryType", "entryArgs"])
    timeStamp = round(time.time() * 1000)

    entryArgs = json.loads(rawEntryArgs)
    
    if entryType == "createTile":
        if entryArgs.get("tileID") == None:
            tileID = incTileCounter(pIDstring)
            entryArgs["tileID"] = tileID

    projectHistoryItem.update({
        'projectID': pID,
        'entryType': entryType,
        'entryArgs': json.dumps(entryArgs),
        'ts': timeStamp
    })

    DSC.put(projectHistoryItem)

    return addToDivCoData(pID, entryType, entryArgs)



def addToDivCoData(pID, entryType, entryArgs):
    returnMessage = {}

    if entryType == "createTile":
        tileID = entryArgs.get("tileID")

        projectTileData = datastore.Entity(key=DSC.key('projectTileData', str(pID) + "#" + str(tileID)))

        label = entryArgs.get("label")
        parentID = entryArgs.get("parentID")
        status = 0# entryArgs.get("status")

        parentPath = []
        if parentID != None:
            parentTileData = getTileDataNode(pID, parentID)
            parentPath.extend(parentTileData["parentPath"])

            order = getlastTileOrder(parentID) + 1
        else:
            order = 1
        
        parentPath.append(tileID)

        projectTileData.update({
            "tileID": tileID,
            "projectID": pID,

            "parentID": parentID,
            "parentPath": parentPath,
            "stepCounter": len(parentPath),

            "label": label,
            "status": status,
            "autoStatus": 0,
            "order": order
        })

        DSC.put(projectTileData)

        returnMessage["status"] = True
        returnMessage["tileChange"] = [projectTileData]

    elif entryType == "updateTile":
        tileID = entryArgs.get("tileID")

        projectTileData = getTileDataNode(pID, tileID)
        
        updateDict = {}
        newParentID = entryArgs.get("parentID")
        if newParentID != None:
            updateDict["parentID"] = newParentID

        newLabel = entryArgs.get("label")
        if newLabel != None:
            updateDict["label"] = newLabel

        newStatus = entryArgs.get("status")
        if newStatus != None:
            updateDict["status"] = newStatus

        newAutoStatus = entryArgs.get("autoStatus")
        if newAutoStatus != None:
            updateDict["autoStatus"] = newAutoStatus

        newOrder = entryArgs.get("order")
        if newOrder != None:
            updateDict["order"] = newOrder

        projectTileData.update(updateDict)
        DSC.put(projectTileData)

        returnMessage["status"] = True
    elif entryType == "deleteTile":
        tileID = entryArgs.get("tileID")

        DSC.delete(DSC.key('projectTileData', str(pID) + "#" + str(tileID)))
        returnMessage["status"] = True
    elif entryType == "reorderTile":
        tileID = entryArgs.get("tileID")
        order = entryArgs.get("order")

        tileData = getTileDataNode(pID, tileID)

        if tileData:
            reorderTile(tileData["parentID"], tileID, order)

        returnMessage["status"] = True
    
    return returnMessage

def getlastTileOrder(parentID):
    queryTileData = DSC.query(kind='projectTileData')
    queryTileData.add_filter('parentID', '=', parentID)

    queryTileData.order = ['-order']
    
    itemList = queryTileData.fetch(1)
    order = 0

    for item in itemList:
        order = item["order"]
    
    return order

def reorderTile(parentID, tileID, newOrder):
    queryTileData = DSC.query(kind='projectTileData')
    queryTileData.add_filter('parentID', '=', parentID)

    queryTileData.order = ['order']
    
    afterOrder = newOrder + 1
    itemList = queryTileData.fetch(1000)

    batch = DSC.batch()
    with batch:
        for item in itemList:
            itemCurOrder = item["order"]
            itemTileID = item["tileID"]

            if itemTileID == tileID:
                item.update({"order": newOrder})
                batch.put(item)
            elif itemCurOrder < newOrder:
                continue
            else:
                item.update({"order": afterOrder})
                batch.put(item)
                afterOrder = afterOrder + 1


def getTileDataTree(projectID, TLTileID, stepLimit):
    queryTileData = DSC.query(kind='projectTileData')
    queryTileData.add_filter('projectID', '=', projectID)
    queryTileData.add_filter('parentPath', '=', TLTileID)
    queryTileData.add_filter('stepCounter', '<=', stepLimit)

    itemList = queryTileData.fetch(1000)

    dataList = []
    for item in itemList:
        dataItem = getTransFormat(item)

        dataList.append(dataItem)

    return dataList

def getTileDataNode(projectID, tileID):
    return DSC.get(DSC.key('projectTileData', str(projectID) + "#" + str(tileID)))

def getTransFormat(tileDataItem):
    dataItem = {}

    dataItem["tileID"] = tileDataItem["tileID"]
    dataItem["parentID"] = tileDataItem["parentID"]
    dataItem["label"] = tileDataItem["label"]
    dataItem["status"] = tileDataItem["status"]
    dataItem["order"] = tileDataItem["order"]

    return dataItem

def getUserByCredentials(email, password):
    queryUser = DSC.query(kind='user')
    queryUser.add_filter('email', '=', email)
    queryResult = queryUser.fetch(1)

    promtedUserEntry = None
    for item in queryResult:
        promtedUserEntry = item
    
    if promtedUserEntry == None:
        return None
    
    salt = promtedUserEntry["salt"]
    saltedPass = promtedUserEntry["password"]

    inputString = salt + password
    sha256Generator = hashlib.sha256()
    sha256Generator.update(inputString.encode('utf-8'))
    submittedSaltedPass = sha256Generator.hexdigest()

    if saltedPass == submittedSaltedPass:
        return {"userID": promtedUserEntry.key.id, "userName" : promtedUserEntry["name"]}
    else:
        return None

def createLoginSession(userID, authToken):
    loginSessionEntry = datastore.Entity(key=DSC.key('loginSession', userID))

    loginSessionEntry.update({
        "userID": userID,
        "created": datetime.datetime.now(),
        "expiration": datetime.datetime.now() + datetime.timedelta(hours=2),

        "authToken": authToken
    })

    DSC.put(loginSessionEntry)

def getUserByLoginSession(authToken):
    queryLoginSession = DSC.query(kind='loginSession')
    queryLoginSession.add_filter('authToken', '=', authToken)
    queryResult = queryLoginSession.fetch(1)

    loginSesionItem = None
    for item in queryResult:
        loginSesionItem = item
    
    userID = loginSesionItem["userID"]  
    userItem = DSC.get(DSC.key('user', userID))
    
    return userItem

def refreshLoginSession(authToken, expiration):
    queryLoginSession = DSC.query(kind='loginSession')
    queryLoginSession.add_filter('authToken', '=', authToken)
    queryResult = queryLoginSession.fetch(1)

    loginSesionItem = None
    for item in queryResult:
        loginSesionItem = item
    
    if loginSesionItem:
        loginSesionItem.update({
            "expiration": expiration
        })

        DSC.put(loginSesionItem)

def clearLoginSession(authToken):
    if authToken:
        queryLoginSession = DSC.query(kind='loginSession')
        queryLoginSession.add_filter('authToken', '=', authToken)
        queryLoginSession.keys_only()

        queryResult = queryLoginSession.fetch(1)

        for item in queryResult:
            DSC.delete(item.key)


def test():
    email = "test@wathever.com"
    name = "HailoTest"
    password = "ged"

    queryUser = DSC.query(kind='user')
    queryUser.add_filter('email', '=', email)
    queryResult = queryUser.fetch(1)
    
    createEntry = True
    for item in queryResult:
        createEntry = False

    if createEntry:
        userEntry = datastore.Entity(key=DSC.key('user'))

        salt = Toolbox.createSalt()

        inputString = salt + password
        sha256Generator = hashlib.sha256()
        sha256Generator.update(inputString.encode('utf-8'))
        saltedPass = sha256Generator.hexdigest()


        datetime.datetime.now()
        userEntry.update({
            "created": datetime.datetime.now(),
            "updated": datetime.datetime.now(),

            "email": email,
            "name": name,
            "salt": salt,
            "password": saltedPass
        })

        DSC.put(userEntry)

        print("test")
    else:
        print("skip")
# class ProjectHistory(ndb.Model):
#     pid = ndb.IntegerProperty()
#     ts = ndb.DateTimeProperty(auto_now=True)
#     eventType = ndb.StringProperty()
#     eventData = ndb.TextProperty()

# class DivCoTileData(ndb.Model):
#     projectID = ndb.IntegerProperty()
#     tileID = ndb.IntegerProperty()

#     topLevelPath = ndb.IntegerProperty(repeated=True)
    
#     status = ndb.IntegerProperty()
#     label = ndb.StringProperty()
    
#     # ordering = ndb.IntegerProperty()
    
#     # stepCounter = ndb.IntegerProperty()
#     # forcedStatus = ndb.BooleanProperty()

# class DivcoProjectDataManager():
#     def __init__(self):
#         pass
    
#     def initDivcoServer(self):
#         uniqueS = "A_Project"

#         counter = Counter(id=uniqueS)
#         counter.put()

#     def createProject(self):
#         uniqueS = "P" + str(allocProjectID())

#         counter = Counter(id=uniqueS)
#         counter.put()

# class DivcoTileDataManager():
#     def __init__(self, projectID):
#         self.projectID = projectID
#         self.cachedTiles = {}
    
#     ## HELPER FUNC
#     def setCacheTile(self, tileDataItem):
#         uniqueS = "%s_%s" % (self.projectID, tileDataItem.tileID)

#         self.cachedTiles[uniqueS] = tileDataItem

#     def getTile(self, tileID):
#         tile = self.cachedTiles.get(tileID)
        
#         if tile:
#             return tile
#         else:
#             uniqueS = "%s_%s" % (self.projectID, tileID)
#             return DivCoTileData.get_by_id(uniqueS)

#     # def createTile(self, parentID):
#     #     tileID = allocTileID(self.projectID)
#     #     uniqueS = "%s_%s" % (self.projectID, tileID)

#     #     tileDataItem = DivCoTileData(id=uniqueS)
#     #     if (parentID == None){
#     #         tileDataItem.topLevelPath = [tileID]
#     #     } else {
#     #         self.getTile()
#     #     }
        
#     #     tileDataItem.tileID = tileID
#     #     tileDataItem.projectID = self.projectID

#     #     return tileDataItem

#     # def updateTile(self, deltaTileDict):
#     #     tileID = deltaTileDict.pop("tileID")

#     #     if tileID == None:
#     #         tileData = self.createTile()
#     #     else:
#     #         tileData = self.getTile(tileID)

#     #     for key, value in deltaTileDict.items():
#     #         setattr(tileData, key, value)
        
#     #     self.setCacheTile(tileData)





#     # def modifyTile(self, deltaTileState):
#     #     if deltaTileState["tileID"] == None:
#     #         freeTileID = 3 #getNextTileID(self.projectID)
#     #         assignTileID = freeTileID
#     #     else:
#     #         assignTileID = deltaTileState["tileID"]

#     #     parentID = deltaTileState["parent"]
        
#         # uniqueS = "%s_%s" % (self.projectID, assignTileID)
#         # tileDataItem = DivCoTileData(id=uniqueS)

#     #     tileDataItem.projectID = self.projectID
#     #     tileDataItem.tileID = assignTileID
        
#     #     if parentID:
#     #         parentTile = self.getTile(parentID)
#     #         topLevelPath = []
#     #         topLevelPath.extend(parentTile.topLevelPath)
#     #         topLevelPath.append(assignTileID)
            
#     #         tileDataItem.topLevelPath = topLevelPath
#     #     else:
#     #         tileDataItem.topLevelPath = [assignTileID]
#     #         # tileItem.stepCounter = 1
        
#     #     tileDataItem.status = deltaTileState["status"]
#     #     tileDataItem.label = deltaTileState["label"]
        
#     #     self.setCacheTile(tileDataItem)
        
#     #     # newLogEvent = tileLog.newLogEvent("insertTile", self.projectID, self.curTimeStamp, parseToJson(tileItem))
#     #     # self.newLogEntries.append(newLogEvent)

#     #     return self.projectID
    
#     # def submitUpdates(self):
#     #     putList = self.cachedTiles.values()
#     #     ndb.put_multi(putList)
        
#     #     del self.cachedTiles