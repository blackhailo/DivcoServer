import time
import json

from google.cloud import datastore
DSC = datastore.Client()

### GLOBAL
def initDivco():
    pCounter = datastore.Entity(key=DSC.key('Counter', "pCounter"))
    pCounter.update({
        'count': 0
    })

    DSC.put(pCounter)

def incProjectCounter():
    currentCount = None
    with DSC.transaction():
        pCounter = DSC.get(DSC.key('Counter', "pCounter"))
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
    tileDataQuery.add_filter('projectID', '=', 3)
    tileDataQuery.keys_only()

    queryHistory = DSC.query(kind='projectHistory')
    queryHistory.add_filter('projectID', '=', 3)
    queryHistory.keys_only()
    
    batch = DSC.batch()
    with batch:
        batch.delete(projectMetaKey)
        for item in tileDataQuery.fetch():
            batch.delete(item.key)
        for item in queryHistory.fetch():
            batch.delete(item.key)

def incTileCounter(projectID):
    currentCount = None

    with DSC.transaction():
        projectMetaItem = DSC.get(DSC.key('projectMeta', projectID))
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
            tileID = incTileCounter(pID)
            entryArgs["tileID"] = tileID

    projectHistoryItem.update({
        'projectID': pID,
        'entryType': entryType,
        'entryArgs': json.dumps(entryArgs),
        'ts': timeStamp
    })

    DSC.put(projectHistoryItem)
    addToDivCoData(pID, entryType, entryArgs)



def addToDivCoData(pID, entryType, entryArgs):
    if entryType == "createTile":
        tileID = entryArgs.get("tileID")
        projectTileData = datastore.Entity(key=DSC.key('projectTileData', str(pID) + "#" + str(tileID)))

        label = entryArgs.get("label")
        parentID = entryArgs.get("parentID")
        status = 0# entryArgs.get("status")

        parentPath = []
        if parentID != None:
            parentTileData = DSC.get(DSC.key('projectTileData', str(pID) + "#" + str(parentID)))
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
    elif entryType == "updateTile":
        tileID = entryArgs.get("tileID")

        projectTileData = DSC.get(DSC.key('projectTileData', str(pID) + "#" + str(tileID)))
        
        updateDict = {}
        newParentID = entryArgs.get("parentID", False)
        if newParentID != False:
            updateDict["parentID"] = newParentID

        newLabel = entryArgs.get("label", False)
        if newLabel != False:
            updateDict["label"] = newLabel

        newStatus = entryArgs.get("status", False)
        if newStatus != False:
            updateDict["status"] = newStatus

        newAutoStatus = entryArgs.get("autoStatus", False)
        if newAutoStatus != False:
            updateDict["autoStatus"] = newAutoStatus

        newOrder = entryArgs.get("order", False)
        if newOrder != False:
            updateDict["order"] = newOrder

        projectTileData.update(updateDict)
        DSC.put(projectTileData)
    elif entryType == "deleteTile":
        tileID = entryArgs.get("tileID")

        DSC.delete(DSC.key('projectTileData', str(pID) + "#" + str(tileID)))
    elif entryType == "reorderTile":
        tileID = entryArgs.get("tileID")
        order = entryArgs.get("order")

        tileData = DSC.get(DSC.key('projectTileData', str(pID) + "#" + str(tileID)))

        if tileData:
            reorderTile(tileData["parentID"], tileID, order)


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

#     def addToProjectHistory(self, jsonString):
#         projectHistoryItem = ProjectHistory()

#         projectHistoryItem.pid = self.projectID
#         projectHistoryItem.eventType = "createTile"
#         projectHistoryItem.eventData = jsonString

#         projectHistoryItem.put()

#     def updateProjectState(self):
#         pass

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