import psycopg2
import os
from urllib.parse import urlparse
import json
import config
import functools
import random

# This might come in handy later:
#   SELECT u.username, STRING_AGG(r.role, ',')
#   FROM users u
#   LEFT JOIN roles r ON (u.userid = r.userid)
#   WHERE u.userid=1;

# Error rollback everywhere
# TODO: logging

DATABASE_URL = os.environ["DATABASE_URL"]

result = urlparse(DATABASE_URL)
POSTGRES_USER = result.username
POSTGRES_PW = result.password
POSTGRES_DB = result.path[1:]
POSTGRES_PORT = result.port
POSTGRES_HOST = result.hostname

def openConn():
    return psycopg2.connect("dbname='%s' user='%s' host='%s' port='%s' password='%s'" %
        (POSTGRES_DB, POSTGRES_USER, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_PW))

CONNECTION = openConn()

def getConn():
    global CONNECTION
    if CONNECTION.closed:
        CONNECTION = openConn()
    return CONNECTION

def ErrorRollback(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        try:
            return func(*a, **kw)
        except:
            print("ROLLING BACK")
            getConn().rollback()
            raise    
    return wrapper

def toUserJson(record):
    return {
        "userid": record[0],
        "displayname": record[1],
        "email": record[2],
        "setup_state": record[3],
        "ts": record[4]
    }

def toBookJson(record):
    return {
        "bookid": record[0],
        "userid": record[1],
        "booktitle": record[2],
        "link1": record[3],
        "link2": record[4],
        "numpdfpages": record[5]
    }

@ErrorRollback
def getBook(bookid):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT bookid, userid, booktitle, link1, link2, numpdfpages
        FROM books WHERE bookid=%s""", (bookid,))
    result = c.fetchone()
    
    # TODO: raise exception?
    if not result:
        c.close()
        conn.commit()
        return None

    book = toBookJson(result)

    # pdfid = book["pdfid"]

    # c.execute("""
    #     SELECT bits
    #     FROM pdfs WHERE pdfid=%s""", (pdfid,))
    # result = c.fetchone()
    # if not result:
    #     c.close()
    #     conn.commit()
    #     return None
    # book["bits"] = result[0]

    c.close()
    conn.commit()

    return book

# Returns True if success
@ErrorRollback
def updateBook(bookid, userid, booktitle, link1, link2, smallpages, largepages):
    conn = getConn()
    c = conn.cursor()

    # c.execute("""
    #     INSERT INTO pdfs
    #     (userid, bits)
    #     VALUES (%s, %s) """, (userid, filepdf))

    #c.execute("SELECT MAX(pdfid) FROM pdfs")
    #result = c.fetchone()
    #pdfid = result[0]

    c.execute("""
        UPDATE books
        SET booktitle=%s, link1=%s, link2=%s, numpdfpages=%s
        WHERE bookid=%s AND userid=%s""", (booktitle, link1, link2, len(smallpages), bookid, userid))

    rowcount = c.rowcount

    if rowcount != 1:
        return False

    pagenum = 0
    for page in smallpages:
        pagenum += 1
        c.execute("""
        INSERT INTO pdfimgs
        (userid, bookid, pagenum, size, bits)
        VALUES (%s, %s, %s, 'SMALL', %s) """, (userid, bookid, pagenum, page))

    pagenum = 0
    for page in largepages:
        pagenum += 1
        c.execute("""
        INSERT INTO pdfimgs
        (userid, bookid, pagenum, size, bits)
        VALUES (%s, %s, %s, 'LARGE', %s) """, (userid, bookid, pagenum, page))
    
    c.close()
    conn.commit()

    return True;

@ErrorRollback
def insertNewReviewBook(userid, bookid, reviewtext):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO reviews
        (userid, bookid, reviewtext)
        VALUES (%s, %s, %s) """, (userid, bookid, reviewtext))

    c.close()
    conn.commit()

@ErrorRollback
def getReview(userid, bookid):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        SELECT reviewtext
        FROM reviews WHERE userid=%s AND bookid=%s
        ORDER BY reviewid DESC""", (userid, bookid))

    result = c.fetchone()
    if result != None:
        reviewtext = result[0]
    else:
        reviewtext = None

    c.close()
    conn.commit()

    return reviewtext



@ErrorRollback
def insertNewBook(userid, booktitle, link1, link2, smallpages, largepages):
    conn = getConn()
    c = conn.cursor()

    # c.execute("""
    #     INSERT INTO pdfs
    #     (userid, bits)
    #     VALUES (%s, %s) """, (userid, filepdf))

    #c.execute("SELECT MAX(pdfid) FROM pdfs")
    #result = c.fetchone()
    #pdfid = result[0]

    c.execute("""
        INSERT INTO books
        (userid, booktitle, link1, link2, numpdfpages)
        VALUES (%s, %s, %s, %s, %s) """, (userid, booktitle, link1, link2, len(smallpages)))

    #result = int(c.fetchone()[0])
    c.execute("SELECT MAX(bookid) FROM books")
    result = c.fetchone()
    bookid = result[0]

    pagenum = 0
    for page in smallpages:
        pagenum += 1
        c.execute("""
        INSERT INTO pdfimgs
        (userid, bookid, pagenum, size, bits)
        VALUES (%s, %s, %s, 'SMALL', %s) """, (userid, bookid, pagenum, page))

    pagenum = 0
    for page in largepages:
        pagenum += 1
        c.execute("""
        INSERT INTO pdfimgs
        (userid, bookid, pagenum, size, bits)
        VALUES (%s, %s, %s, 'LARGE', %s) """, (userid, bookid, pagenum, page))
    
    c.close()
    conn.commit()

    return bookid;

@ErrorRollback
def getImg(bookid, size, pagenum):

    conn = getConn()
    c = conn.cursor()

    c.execute("""
        SELECT numpdfpages
        FROM books WHERE bookid=%s""", (bookid,))

    # TODO: what if there is no result?
    numpdfpages = int(c.fetchone()[0])

    if pagenum < 1 or pagenum > numpdfpages:
        return None
    
    c.execute("""
        SELECT bits
        FROM pdfimgs WHERE bookid=%s AND size=%s AND pagenum=%s
        ORDER BY pdfimgid DESC""", (bookid, size, pagenum))

    # TODO: what if there is no result?
    result = c.fetchone()[0]
    c.close()
    conn.commit()

    return result

@ErrorRollback
def getNumRegisteredUsers():
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(userid)
        FROM users WHERE setup_state='EMAIL_CONFIRMED'""")

    # TODO: what if there is no result?
    result = int(c.fetchone()[0])
    
    c.close()
    conn.commit()

    return result
    

@ErrorRollback
def getConfirmedUserByUserid(userid):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, displayname, email, setup_state, ts
        FROM users WHERE userid=%s AND setup_state='EMAIL_CONFIRMED'""", (userid,))
    result = c.fetchone()
    
    # TODO: raise exception?
    if not result:
        c.close()
        conn.commit()
        return None

    user = toUserJson(result)

    c.execute("""
        SELECT role FROM roles WHERE userid=%s""", (user["userid"],))
    user["roles"] = [r[0] for r in c.fetchall()]

    c.close()
    conn.commit()

    return user

@ErrorRollback
def getConfirmedUsersByUserids(userids):
    results = []
    for userid in userids:
        result = getConfirmedUserByUserid(userid)
        if result:
            results.append(result)
        else:
            pass # TODO: raise exception
    return results

class ShouldBeImpossible(Exception):
    pass

class MultipleConfirmedAccounts(Exception):
    pass

# IMPORTANT NOTE: the roles field will not exist within results
@ErrorRollback
def getAllUsersForAnySetupStateByEmail(email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, displayname, email, setup_state, ts
        FROM users WHERE email=%s""", (email,))
    results = c.fetchall()
    c.close()
    conn.commit()

    if not results:
        return []

    results = [toUserJson(record) for record in results]

    if len(results) == 0:
        raise ShouldBeImpossible

    numConfirmed = 0
    for record in results:
        if record["setup_state"] == "EMAIL_CONFIRMED":
            numConfirmed += 1

    if numConfirmed > 1:
        raise MultipleConfirmedAccounts

    return results

@ErrorRollback
def createUnconfirmedAccount(displayname, email, referUserid):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO users
        (displayname, email, refer, setup_state)
        VALUES (%s, %s, %s, 'CONFIRMATION_EMAIL_SENT') """, (displayname, email, referUserid))

    c.execute("SELECT MAX(userid) FROM users")
    result = c.fetchone()
    useridInt = result[0]
    c.close()
    conn.commit()

    # NOTE: userids are always of type of string, even though they just hold a number
    # This is convenient because SESSION["userid"] will always be a string
    return str(useridInt)

class UpdatePasswordByEmailError(Exception):
    pass

# IMPORTNANT NOTE: the returned user dict will not have a role field
@ErrorRollback
def getUnconfirmedUserByEmail(email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, displayname, email, setup_state, ts
        FROM users WHERE email=%s""", (email,))
    result = c.fetchone()
    c.close()
    conn.commit()

    if not result:
        return None
    else:
        return toUserJson(result)



class ConfirmEmailErrorRowCountNotOne(Exception):
    pass

@ErrorRollback
def confirmEmail(email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        UPDATE users
        SET setup_state='EMAIL_CONFIRMED'
        WHERE email=%s;""", (email,))
    rowcount = c.rowcount
    if rowcount != 1:
        c.close()
        conn.rollback()
        raise ConfirmEmailErrorRowCountNotOne

    c.execute("""
        UPDATE users
        SET setup_state='RETIRED'
        where email=%s AND setup_state != 'EMAIL_CONFIRMED';
        """, (email, ))

    c.close()
    conn.commit()

@ErrorRollback
def getConfirmedUserByEmail(email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, displayname, email, setup_state, ts
        FROM users WHERE email=%s AND setup_state='EMAIL_CONFIRMED'""", (email,))
    result = c.fetchone()
    
    # TODO: raise exception?
    if not result:
        c.close()
        conn.commit()
        return None

    user = toUserJson(result)

    c.execute("""
        SELECT role FROM roles WHERE userid=%s""", (user["userid"],))
    user["roles"] = [r[0] for r in c.fetchall()]

    c.close()
    conn.commit()

    return user

# TODO: race condition
@ErrorRollback
def markTokenUsed(token):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO usedtokens
        (token)
        VALUES (%s) """, (token,))
    c.close()
    conn.commit()

# TODO: race condition
@ErrorRollback
def hasTokenBeenUsed(token):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT usedtokenid
        FROM usedtokens where token=%s""", (token,))
    result = c.fetchone()
    c.close()
    conn.commit()

    if result:
        return True
    else:
        return False
