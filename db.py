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

def doGetRandomBooks(books, maxBooks):
    #numBooks = len(books)

    numBooks = min(len(books), maxBooks)

    if numBooks == 0:
        return []

    random.shuffle(books)
    print(books)
    totalPoints = sum([b["points"] for b in books])

    selected = []

    selectedBookids = set([])

    for _ in range(0, numBooks):
        #for b in books:
    
        doLoop = True

        # Keep looping until we select an unselected book
        while doLoop:
            targetPoint = random.uniform(0.0, totalPoints)
            rightside = books[0]["points"]
            didselect = False
            leftside = 0.0
        
            bookselect = None
            for i in range(0, numBooks - 1):
                b = books[i]
                if targetPoint >= leftside and targetPoint <= rightside:
                    bookselect = b #selected.append(b)
                    didselect = True
                    break
                leftside = rightside
                rightside += books[i+1]["points"]

            if not didselect:
                #raise Exception("bad")
                #selected.append(books[-1])
                bookselect = books[-1]

            if bookselect["bookid"] not in selectedBookids:
                selectedBookids.add(bookselect["bookid"])
                doLoop = False

        selected.append(bookselect)


    return selected

def test0():
    result = doGetRandomBooks([], 5)
    if len(result) != 0:
        raise Exception("test0 fail")

def test1():
    books = [{"points": 4.7, "bookid": 1}]

    for _ in range(0, 100):
        result = doGetRandomBooks(books, 5)
        if len(result) != 1:
            raise Exception("test1 fail")
        if result[0]["bookid"] != 1:
            raise Exception("test1 fail")

def test2():
    books = [
        {"points": 2.0, "bookid": 1},
        {"points": 3.0, "bookid": 2}
    ]

    iterations = 100000
    num1 = 0.0
    num2 = 0.0
    for _ in range(0, iterations):
        result = doGetRandomBooks(books, 5)
        if len(result) != 2:
            raise Exception("test2 fail")
        if result[0]["bookid"] == 1:
            num1 += 1
            if result[1]["bookid"] != 2:
                raise Exception("test2 fail a: " + str(result[1]["bookid"]))
        elif result[0]["bookid"] == 2:
            num2 += 1
            if result[1]["bookid"] != 1:
                raise Exception("test2 fail b: " + str(result[1]["bookid"]))
        else:
            raise Exception("test2 fail")

    p1 = num1 / iterations

    if round(p1, 2) != 2.0 / 5.0:
        raise Exception("test2 fail c" + str(round(p1, 2)))


def test3():
    books = [
        {"points": 1.0, "bookid": 1},
        {"points": 2.0, "bookid": 2},
        {"points": 3.0, "bookid": 3},
    ]

    iterations = 100000

    # probability when book 1 is in ith slot
    slots = [0.0, 0.0, 0.0]
    for _ in range(0, iterations):
        result = doGetRandomBooks(books, 5)
        if len(result) != 3:
            raise Exception("test3 fail")
        if result[0]["bookid"] == 1:
            slots[0] += 1
            if result[1]["bookid"] == 2:
                if result[2]["bookid"] != 3:
                    raise Exception("test3 fail")
            elif result[1]["bookid"] == 3:
                if result[2]["bookid"] != 2:
                    raise Exception("test3 fail")
            else:
                raise Exception("test3 fail")
        elif result[0]["bookid"] == 2:
            if result[1]["bookid"] == 1:
                slots[1] += 1
                if result[2]["bookid"] != 3:
                    raise Exception("test3 fail")
            elif result[1]["bookid"] == 3:
                slots[2] += 1
                if result[2]["bookid"] != 1:
                    raise Exception("test3 fail")
            else:
                raise Exception("test3 fail")
        elif result[0]["bookid"] == 3:
            if result[1]["bookid"] == 1:
                slots[1] += 1
                if result[2]["bookid"] != 2:
                    raise Exception("test3 fail")
            elif result[1]["bookid"] == 2:
                slots[2] += 1
                if result[2]["bookid"] != 1:
                    raise Exception("test3 fail")
            else:
                raise Exception("test3 fail")
        else:
            raise Exception("test2 fail")

    #targets = [1.0 / 6.0, 2.0 / 6.0, 3.0 / 6.0]
    ps = [p / float(iterations) for p in slots]

    # for each book
    #for i in range(0, 3):
    #    num = nums[i]
    #    bookid = i + 1



    #if round(p1, 2) != 2.0 / 5.0:
    #    raise Exception("test2 fail c" + str(round(p1, 2)))



def testDoGetRandomBooks():
    test0()
    test1()
    test2()
    test3()


#testDoGetRandomBooks()


def toRbookJson(record):
    print(record)
    return {
        "bookid": record[0],
        "userid": record[1],
        "booktitle": record[2],
        "points": record[3],
    }

@ErrorRollback
def getRandomBooks(maxBooks):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT b.bookid, b.userid, b.booktitle, u.points
        FROM books b LEFT JOIN users u on b.userid=u.userid
        """)
    results = c.fetchall()

    if results == None:
        return None

    books = [toRbookJson(r) for r in results]

    return  doGetRandomBooks(books, maxBooks)




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
def calcPoints(userid):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(bookid)
        FROM books WHERE userid=%s""", (userid,))

    result = c.fetchone()
    if result:
        numBooks = int(result[0])
    else:
        numBooks = 0

    c.execute("""
        SELECT COUNT(bookid)
        FROM books""")

    result = c.fetchone()
    if result:
        numTotalBooks = int(result[0])
    else:
        numTotalBooks = 0

    c.execute("""
    SELECT COUNT(DISTINCT(bookid))
    FROM reviews WHERE userid=%s""", (userid,))

    result = c.fetchone()
    if result:
        #numReviews = len(result)
        numReviews = int(result[0])
    else:
        numReviews = 0

    c.execute("""
    SELECT COUNT(DISTINCT(CONCAT(bookid,userid)))
    FROM reviews""")
    result = c.fetchone()
    if result:
        numTotalReviews = int(result[0])
    else:
        numTotalReviews = 0

    c.close()
    conn.commit()

    return {
        "numBooks": numBooks,
        "numReviews": numReviews,
        "numTotalBooks": numTotalBooks,
        "numTotalReviews": numTotalReviews
    }

def updatePoints(c, userid):

    c.execute("""
        SELECT COUNT(bookid)
        FROM books WHERE userid=%s""", (userid,))

    result = c.fetchone()
    if result:
        numBooks = int(result[0])
    else:
        numBooks = 0

    if numBooks == 0:
        points = 0.0
    else:
        c.execute("""
        SELECT COUNT(DISTINCT(bookid))
        FROM reviews WHERE userid=%s""", (userid,))

        result = c.fetchone()
        if result:
            #numReviews = len(result)
            numReviews = int(result[0])
        else:
            numReviews = 0


        points = float(numReviews + numBooks) / float(numBooks)

    c.execute("""
        UPDATE users
        SET points=%s
        WHERE userid=%s;""", (points, userid))

# And updates points
@ErrorRollback
def insertNewReviewBook(userid, bookid, reviewtext):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO reviews
        (userid, bookid, reviewtext)
        VALUES (%s, %s, %s) """, (userid, bookid, reviewtext))

    updatePoints(c, userid)

    c.close()
    conn.commit()



def toMyBookJson(record):
    return {
        "bookid": record[0],
        "booktitle": record[1]
    }

@ErrorRollback
def getMyBooks(userid):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        SELECT bookid, booktitle
        FROM books WHERE userid=%s
        ORDER BY bookid DESC""", (userid,))

    results = c.fetchall()
    results = [toMyBookJson(record) for record in results]

    for book in results:
        c.execute("""
        SELECT COUNT (DISTINCT userid)
        FROM reviews WHERE bookid=%s""", (book["bookid"],))

        result = c.fetchone()
        if result:
            book["numreviews"] = int(result[0])
        else:
            book["numreviews"] = 0

        c.execute("""
        SELECT COUNT (DISTINCT r.userid)
        FROM reviews r
        LEFT JOIN reviewperms rp ON rp.bookid=r.bookid AND rp.userid=r.userid
        WHERE r.bookid=%s AND rp.perm='PUBLIC' """, (book["bookid"],))

        result = c.fetchone()
        if result:
            book["numpublicreviews"] = int(result[0])
        else:
            book["numpublicreviews"] = 0


            
    c.close()
    conn.commit()

    return results

def toMyReviewsJson(record):
    return {
        "reviewid": record[0],
        "reviewtext": record[1],
        "booktitle": record[2],
        "bookid": record[3],
    }
   

@ErrorRollback
def getMyReviews(userid):
    conn = getConn()
    c = conn.cursor()


    c.execute("""
        SELECT r.reviewid, r.reviewtext, b.booktitle, b.bookid
        FROM reviews r LEFT JOIN books b ON b.bookid=r.bookid
        WHERE r.userid=%s
        ORDER BY r.reviewid DESC""", (userid,))
        #ORDER BY r.reviewid DESC""", (userid,))

    results = c.fetchall()

    #results = filter(lambda r: , results)
    results = [toMyReviewsJson(record) for record in results]

    reviewids = set([])
    reviews = []
    for r in results:
        if r["bookid"] not in reviewids:
            reviewids.add(r["bookid"])
            reviews.append(r)


    c.close()
    conn.commit()

    return reviews



def toAllReviewsJson(record):
    return {
        "reviewid": record[0],
        "reviewtext": record[1],
        "userid": record[2],
        "displayname": record[3],
        "perm": record[4]
    }

def getAllReviews(bookid):

    conn = getConn()
    c = conn.cursor()

    c.execute("""
        SELECT DISTINCT ON (r.userid) r.reviewid, r.reviewtext, r.userid, u.displayname, rp.perm
        FROM reviews r
        LEFT JOIN users u on u.userid=r.userid
        LEFT JOIN reviewperms rp on rp.userid=r.userid AND rp.bookid=r.bookid
        WHERE r.bookid=%s""", (bookid,))

    results = c.fetchall()
    results = [toAllReviewsJson(record) for record in results]

    c.close()
    conn.commit()

    return results


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

# userid is the visitor must make sure it matches
def makeReviewPublicPrivate(userid, bookid, reviewid, public):

    conn = getConn()
    c = conn.cursor()

    c.execute("""
        SELECT b.userid, r.userid
        FROM reviews r
        LEFT JOIN books b ON b.bookid = r.bookid
        WHERE r.reviewid=%s
        """, (reviewid,))

    # Make sure userid matches book owner's id
    result = c.fetchone()
    if result == None:
        abort(403)

    [bookuserid, reviewuserid] = result
    print(result)
    if int(bookuserid) != int(userid):
        abort(403)

    c.execute("""
        DELETE FROM reviewperms WHERE userid=%s AND bookid=%s 
        """, (reviewuserid, bookid))

    if public:
        pstr = "PUBLIC"
        c.execute("""
            INSERT INTO reviewperms (userid, bookid, perm)
            VALUES (%s, %s, %s)""", (reviewuserid, bookid, pstr))

    c.close()
    conn.commit()



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
    
    updatePoints(c, userid)

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
