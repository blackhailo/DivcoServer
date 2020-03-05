from google.appengine.ext import ndb

class DivCoTileData(ndb.Model):
    projectID = ndb.IntegerProperty()
    tileID = ndb.IntegerProperty()

    topLevelPath = ndb.IntegerProperty(repeated=True)
    
    status = ndb.IntegerProperty()
    label = ndb.StringProperty()
    
    # ordering = ndb.IntegerProperty()
    
    # stepCounter = ndb.IntegerProperty()
    # forcedStatus = ndb.BooleanProperty()

class DivcoTileDataManager():
    def __init__(self, projectID):
        self.projectID = projectID
        self.cachedTiles = {}
    
    ## HELPER FUNC
    def setCacheTile(self, tileDataItem):
        uniqueS = "%s_%s" % (self.projectID, tileDataItem.tileID)

        self.cachedTiles[uniqueS] = tileDataItem

    def getTile(self, tileID):
        tile = self.cachedTiles.get(tileID)
        
        if tile:
            return tile
        else:
            uniqueS = "%s_%s" % (self.projectID, tileID)
            return DivCoTileData.get_by_id(uniqueS)

    def createTile(self):
        assignTileID = 2

        uniqueS = "%s_%s" % (self.projectID, assignTileID)
        tileDataItem = DivCoTileData(id=uniqueS)

        return tileDataItem

    def updateTile(self, deltaTileDict):
        tileID = deltaTileDict["tileID"]

        if tileID == None:
            tileData = self.createTile()
        else:
            tileData = self.getTile(tileID)

        for key, value in deltaTileDict.items():
            setattr(tileData, key, value)
        
        self.setCacheTile(tileData)





    # def modifyTile(self, deltaTileState):
    #     if deltaTileState["tileID"] == None:
    #         freeTileID = 3 #getNextTileID(self.projectID)
    #         assignTileID = freeTileID
    #     else:
    #         assignTileID = deltaTileState["tileID"]

    #     parentID = deltaTileState["parent"]
        
        # uniqueS = "%s_%s" % (self.projectID, assignTileID)
        # tileDataItem = DivCoTileData(id=uniqueS)

    #     tileDataItem.projectID = self.projectID
    #     tileDataItem.tileID = assignTileID
        
    #     if parentID:
    #         parentTile = self.getTile(parentID)
    #         topLevelPath = []
    #         topLevelPath.extend(parentTile.topLevelPath)
    #         topLevelPath.append(assignTileID)
            
    #         tileDataItem.topLevelPath = topLevelPath
    #     else:
    #         tileDataItem.topLevelPath = [assignTileID]
    #         # tileItem.stepCounter = 1
        
    #     tileDataItem.status = deltaTileState["status"]
    #     tileDataItem.label = deltaTileState["label"]
        
    #     self.setCacheTile(tileDataItem)
        
    #     # newLogEvent = tileLog.newLogEvent("insertTile", self.projectID, self.curTimeStamp, parseToJson(tileItem))
    #     # self.newLogEntries.append(newLogEvent)

    #     return self.projectID
    
    def submitUpdates(self):
        putList = self.cachedTiles.values()
        ndb.put_multi(putList)
        
        del self.cachedTiles