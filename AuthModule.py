import flask

def validateCookie(allowMissing=False):
    activeCookies = flask.request.cookies

    activeAuthToken = activeCookies.get("DIVCO_AUTH_TOKEN")
    
    if allowMissing:
        return activeAuthToken
    else:
        if activeAuthToken == None:
            flask.abort(401)
        else:
            return activeAuthToken