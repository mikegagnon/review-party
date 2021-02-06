from flask import current_app, session, request

app = current_app

# TODO: put this elsewhere?
def getUserOrAnonymousId():
    if "userid" in session:
        return (session["userid"], None)
    else:
        return (None, "anonymous")

def dolog(f, funcname, message):
    if session:
        (userid, anonymousUserid) = getUserOrAnonymousId()
        if userid:
            email = session["email"]
            f("[userid=%s, email=%s, url=%s, function=%s] %s", userid, email, request.url, funcname, message)
        else:
            f("[anonymousUserid=%s, url=%s, function=%s] %s", anonymousUserid, request.url, funcname, message)
    else:
            f("[outside of request context, function=%s] %s", funcname, message)

def critical(funcname, message):
    dolog(app.logger.critical, funcname, message)

def error(funcname, message):
    dolog(app.logger.error, funcname, message)

def warn(funcname, message):
    dolog(app.logger.warning, funcname, message)

# TODO: dedup
def warning(funcname, message):
    warn(funcname, message)

def info(funcname, message):
    dolog(app.logger.info, funcname, message)

def debug(funcname, message):
    dolog(app.logger.debug, funcname, message)
