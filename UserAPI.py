import os
import codecs
import json
import datetime
import hashlib
import secrets

import flask
import werkzeug.exceptions
from google.cloud import datastore

import DataStore.DivcoDataStore as DivcoDataStore
import AuthModule
from Toolbox import jsonResponse

DSC = datastore.Client()

class UserAPI:
    def __init__(self, app):
        app.add_url_rule('/papi/getUserData', 'getUserData', self.getUserData)

        app.add_url_rule('/papi/doLogin', 'doLogin', self.doLogin, methods=['POST'])
        app.add_url_rule('/papi/doLogout', 'doLogout', self.doLogout)

    def getUserData(self):
        authToken = AuthModule.validateCookie(True)

        if authToken != None:
            activeUserData = DivcoDataStore.getUserByLoginSession(authToken)

            if activeUserData:
                activeUser = {"userID": activeUserData.key.id, "userName" : activeUserData["name"]}
            else:
                activeUser = {}
        else:
            activeUser = {}

        return jsonResponse(activeUser, authToken)
    
    def doLogin(self):
        rawData = flask.request.form

        email = rawData.get("email")
        password = rawData.get("password")

        activeUser = DivcoDataStore.getUserByCredentials(email.lower(), password)
        if activeUser == None:
            flask.abort(401)

        randomComponent = str(secrets.token_hex(16))
        dateComponent = datetime.datetime.now()
        userComponent = str(activeUser)

        inputString = userComponent + randomComponent + str(dateComponent)
        sha256Generator = hashlib.sha256()
        sha256Generator.update(inputString.encode('utf-8'))

        authToken = sha256Generator.hexdigest()

        DivcoDataStore.createLoginSession(activeUser.get("userID"), authToken)

        return jsonResponse(activeUser, authToken)

    def doLogout(self):
        activeAuthToken = AuthModule.validateCookie(True)
        DivcoDataStore.clearLoginSession(activeAuthToken)
        
        return jsonResponse({"msg": "user logged out."}, authToken="")