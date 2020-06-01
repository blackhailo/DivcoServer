import flask
import json
import datetime

import DataStore.DivcoDataStore as DivcoDataStore

def csvResponse(filename, csvData, authToken=None):
    response = flask.Response(csvData, content_type="text/csv; charset=utf-8")

    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Request-Headers'] = 'Origin, Content-Type'

    response.headers['Content-Disposition'] = 'attachment; filename=' + filename
    
    response.headers['Vary'] = 'Origin'

    if authToken == "":
        response.set_cookie("DIVCO_AUTH_TOKEN", "", expires=0, samesite="Strict")
    elif authToken:
        expiration = datetime.datetime.now() + datetime.timedelta(hours=2)

        DivcoDataStore.refreshLoginSession(authToken, expiration)
        response.set_cookie("DIVCO_AUTH_TOKEN", authToken, expires=expiration.timestamp(), samesite="Strict")

    return response

def jsonResponse(responseDict, authToken=None):
    response = flask.Response(json.dumps(responseDict, sort_keys=True), content_type="application/json")

    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Request-Headers'] = 'Origin, Content-Type'
    
    response.headers['Vary'] = 'Origin'

    if authToken == "":
        response.set_cookie("DIVCO_AUTH_TOKEN", "", expires=0, samesite="Strict")
    elif authToken:
        expiration = datetime.datetime.now() + datetime.timedelta(days=2)

        DivcoDataStore.refreshLoginSession(authToken, expiration)
        response.set_cookie("DIVCO_AUTH_TOKEN", authToken, expires=expiration.timestamp(), samesite="Strict")

    return response