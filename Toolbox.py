import flask
import json
import datetime
import random

import DataStore.DivcoDataStore as DivcoDataStore

def createSalt():
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    salt = ''.join(random.choice(ALPHABET) for i in range(16))

    return salt

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
        expiration = datetime.datetime.now() + datetime.timedelta(hours=2)

        DivcoDataStore.refreshLoginSession(authToken, expiration)
        response.set_cookie("DIVCO_AUTH_TOKEN", authToken, expires=expiration.timestamp(), samesite="Strict")

    return response