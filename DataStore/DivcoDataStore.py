import datetime
import time
import json
import hashlib
import copy
import random

from google.cloud import datastore
DSC = datastore.Client()

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
def createProjectMeta(projectID, name, owner):
    projectMetaItem = datastore.Entity(key=DSC.key('projectMeta', projectID))

    projectMetaItem.update({
        'projectID': projectID,
        'name': name,
        'ownerUserList': [owner],
        'assoUserList': [],
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

    DSC.delete(projectMetaKey)

    deleteList = []

    for item in tileDataQuery.fetch():
        deleteList.append(item.key)

    DSC.delete_multi(deleteList)
    
    deleteList = []
    for item in queryHistory.fetch():
        deleteList.append(item.key)

    DSC.delete_multi(deleteList)


def incTileCounter(pID):
    currentCount = None

    with DSC.transaction():
        projectMetaItem = DSC.get(DSC.key('projectMeta', pID))
        currentCount = projectMetaItem["tileCounter"]

        projectMetaItem.update({
            'tileCounter': currentCount + 1
        })

        DSC.put(projectMetaItem)

    return currentCount + 1

# MAIN DATA-STRUCTURES
def getNewestEntryFromProjectHistory(pID):
    projectHistoryQuery = DSC.query(kind='projectHistory')
    projectHistoryQuery.add_filter('projectID', '=', pID)
    projectHistoryQuery.order = ['-ts']

    itemList = projectHistoryQuery.fetch(1)

    newestItem = None
    for item in itemList:
        newestItem = item

    return newestItem


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

    return addToDivCoData(pID, entryType, entryArgs)

def changeProjectMetaName(pID, name):
    projectMetaItem = DSC.get(DSC.key('projectMeta', pID))
    projectMetaItem.update({"name" : name})
    DSC.put(projectMetaItem)

def addToDivCoData(pID, entryType, entryArgs):
    returnMessage = {}

    if entryType == "createTile":
        tileID = entryArgs.get("tileID")
        
        projectTileData = datastore.Entity(key=DSC.key('projectTileData', str(pID) + "#" + str(tileID)))

        label = entryArgs.get("label")
        parentID = entryArgs.get("parentID")
        status = 0# entryArgs.get("status")

        if tileID == 1:
            changeProjectMetaName(pID, label)
        
        parentPath = []
        if parentID != None:
            # print(entryType, entryArgs)
            parentTileData = getTileDataNode(pID, parentID)
            parentPath.extend(parentTileData["parentPath"])

            order = getlastTileOrder(pID, parentID) + 1
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
        tileIDList = entryArgs.get("tileIDList")
        
        updateGroup = []
        for tileID in tileIDList:
            tileData = getTileDataNode(pID, tileID)
            
            if tileData:
                updateDict = {}
                newParentID = entryArgs.get("parentID")
                if newParentID != None:
                    oldParentID = tileData["parentID"]
                    parentTile = getTileDataNode(pID, newParentID)

                    pathSection = [oldParentID, tileID]
                    matchingParentPathList = getMatchingParentPathList(pID, pathSection)

                    for item in matchingParentPathList:
                        currentPPath = item["parentPath"]
                        newSuperPath = parentTile["parentPath"]
                        indexOfOldParent = currentPPath.index(oldParentID)

                        updatedPath = copy.deepcopy(newSuperPath)
                        updatedPath.extend(currentPPath[indexOfOldParent + 1:])
                        
                        item.update({
                            "parentID" : updatedPath[-2],
                            "parentPath" : updatedPath,
                            "stepCounter" : len(updatedPath)
                        })                   

                        updateGroup.append(item)
                else:
                    newLabel = entryArgs.get("label")
                    if newLabel != None:
                        if tileID == 1:
                            changeProjectMetaName(pID, newLabel)
                        
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

                    tileData.update(updateDict)
                    updateGroup.append(tileData)

        if len(updateGroup) > 0:
            DSC.put_multi(updateGroup)
        
        returnMessage["status"] = True
    elif entryType == "deleteTile":
        tileIDList = entryArgs.get("tileIDList")
        
        batch = DSC.batch()
        with batch:
            for tileID in tileIDList:
                batch.delete(DSC.key('projectTileData', str(pID) + "#" + str(tileID)))

        returnMessage["status"] = True
    elif entryType == "reorderTile":
        updateTileSet = entryArgs.get("updateTileSet")

        batch = DSC.batch()
        with batch:
            for item in updateTileSet:
                tileID = item[0]
                tileOrder = item[1]

                tileData = getTileDataNode(pID, tileID)
                if tileData:
                    tileData.update({"order" : tileOrder})
                    batch.put(tileData)

        returnMessage["status"] = True
    
    return returnMessage

def getChildrenOfTile(projectID, parentID, curStepCounter):
    queryTileData = DSC.query(kind='projectTileData')
    queryTileData.add_filter('projectID', '=', projectID)
    queryTileData.add_filter('parentPath', '=', parentID)
    queryTileData.add_filter('stepCounter', '>', curStepCounter)

    itemList = queryTileData.fetch(1000)
    
    return itemList

def getlastTileOrder(pID, parentID):
    queryTileData = DSC.query(kind='projectTileData')
    queryTileData.add_filter('projectID', '=', pID)
    queryTileData.add_filter('parentID', '=', parentID)

    queryTileData.order = ['-order']
    
    itemList = queryTileData.fetch(1)
    order = 0

    for item in itemList:
        order = item["order"]
    
    return order

def getTileDataTree(projectID, TLTileID, stepLimit):
    queryTileData = DSC.query(kind='projectTileData')
    queryTileData.add_filter('projectID', '=', projectID)
    queryTileData.add_filter('parentPath', '=', TLTileID)
    queryTileData.add_filter('stepCounter', '<=', stepLimit)

    itemList = queryTileData.fetch()

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

def getUserByEmail(email):
    queryUser = DSC.query(kind='user')
    queryUser.add_filter('email', '=', email)
    queryResult = queryUser.fetch(1)

    user = None
    for item in queryResult:
        user = item
    
    return user


def createLoginSession(userID, authToken):
    loginSessionEntry = datastore.Entity(key=DSC.key('loginSession', userID))

    loginSessionEntry.update({
        "userID": userID,
        "created": datetime.datetime.now(),
        "expiration": datetime.datetime.now() + datetime.timedelta(days=2),

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
    
    if loginSesionItem:
        userID = loginSesionItem["userID"]  
        userItem = DSC.get(DSC.key('user', userID))
    
        return userItem
    else:
        return None

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

def createSalt():
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    salt = ''.join(random.choice(ALPHABET) for i in range(16))

    return salt

def createNewUser(name, email, password):
    queryUser = DSC.query(kind='user')
    queryUser.add_filter('email', '=', email)
    queryResult = queryUser.fetch(1)
    
    createEntry = True
    for item in queryResult:
        createEntry = False

    if createEntry:
        userEntry = datastore.Entity(key=DSC.key('user'))

        salt = createSalt()

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
    else:
        # user already exist
        pass

def createNewProject(userID, projectName, pID=None):
    if pID == None:
        pID = incProjectCounter()
    
    createProjectMeta(pID, projectName, userID)

    entryType = "createTile"
    rawEntryArgs = r'{"label":"' + projectName + r'","parentID":null}'
    addToProjectHistory(pID, entryType, rawEntryArgs)

    return pID

def getProjectUserList(pID):
    projectMeta = DSC.get(DSC.key('projectMeta', pID))

    userList = []
    if (projectMeta != None):
        ownerIDList = projectMeta["ownerUserList"]
        userIDList = projectMeta["assoUserList"]

        for userID in ownerIDList:
            userDataItem = DSC.get(DSC.key('user', userID))

            userResponseItem = {}
            userResponseItem["name"] = userDataItem["name"]
            userResponseItem["email"] = userDataItem["email"]
            userResponseItem["rights"] = "owner"

            userList.append(userResponseItem)
        
        for userID in userIDList:
            userDataItem = DSC.get(DSC.key('user', userID))

            userResponseItem = {}
            userResponseItem["name"] = userDataItem["name"]
            userResponseItem["email"] = userDataItem["email"]
            userResponseItem["rights"] = "user"

            userList.append(userResponseItem)

    return userList

def addUserToProject(pID, email, rights):
    projectMeta = DSC.get(DSC.key('projectMeta', pID))

    user = getUserByEmail(email)

    if user:
        if rights == "owner":
            ownerIDList = projectMeta["ownerUserList"]
            ownerIDList.append(user.key.id)
            projectMeta.update({"ownerUserList" : ownerIDList})
        elif rights == "user":
            userIDList = projectMeta["assoUserList"]
            userIDList.append(user.key.id)
            projectMeta.update({"assoUserList" : userIDList})
    
        DSC.put(projectMeta)
    else:
        raise ValueError("User does not exist")

def removeUserFromProject(pID, email):
    projectMeta = DSC.get(DSC.key('projectMeta', pID))

    user = getUserByEmail(email)

    ownerIDList = projectMeta["ownerUserList"]
    for ownerID in ownerIDList:
        if ownerID != user.key.id:
            continue
        elif ownerID == user.key.id and len(ownerIDList) > 1:
            ownerIDList.remove(ownerID)
            projectMeta.update({"ownerUserList" : ownerIDList})
        else:
            raise ValueError("cannot delete the last owner of the project")

    userIDList = projectMeta["assoUserList"]
    for userID in userIDList:
        if userID == user.key.id:
            userIDList.remove(userID)
            projectMeta.update({"assoUserList" : userIDList})

    DSC.put(projectMeta)

def getCompleteProjectHistory(pID):
    # TODO fix for projects with more than 1000 rows
    projectHistoryQuery = DSC.query(kind='projectHistory')
    projectHistoryQuery.add_filter('projectID', '=', pID)
    projectHistoryQuery.order = ['ts']

    queryResult = projectHistoryQuery.fetch()
    
    # convertToCsv
    csvRowList = []
    csvRowList.append(["ts", "entryType", "entryArgs"])
    for item in queryResult:
        ts = item["ts"]
        entryType = item["entryType"]
        entryArgs = item["entryArgs"]

        csvRowList.append([ts, entryType, entryArgs])

    # nextCursor = queryResult.next_page_token
    # print(nextCursor)

    return csvRowList

def getLegacyProjectHistory(pID):
    projectHistoryQuery = DSC.query(kind='LogEvent')
    projectHistoryQuery.add_filter('projectID', '=', pID)
    projectHistoryQuery.order = ['timeStamp']

    queryResult = projectHistoryQuery.fetch()
    
    # convertToCsv
    csvRowList = []
    csvRowList.append(["timeStamp", "eventName", "eventData"])
    for item in queryResult:
        ts = item["timeStamp"]
        entryType = item["eventName"]
        entryArgs = item["eventData"]

        csvRowList.append([ts, entryType, entryArgs])

    nextCursor = queryResult.next_page_token
    print(nextCursor)

    return csvRowList

def getMatchingParentPathList(pID, pathSection):
    queryTileData = DSC.query(kind='projectTileData')
    queryTileData.add_filter('projectID', '=', pID)

    for tileID in pathSection:
        queryTileData.add_filter('parentPath', '=', tileID)

    queryResult = queryTileData.fetch()
    
    return queryResult