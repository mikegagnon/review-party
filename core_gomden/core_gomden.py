# PUNT: better logging
import base64
from io import BytesIO
from PIL import Image

from pdf2image import convert_from_bytes, exceptions
import flask
from flask import *
from flask_wtf import FlaskForm
import json

from urllib.parse import unquote
import json
import cgi

import db
import config
from gomden_log import *
import re

from wtforms import StringField, FileField
from werkzeug.utils import secure_filename

send_email = None
def init(se):
    global send_email
    send_email = se

core_gomden_blueprint = Blueprint('core_gomden_blueprint', __name__, template_folder='templates', static_folder='static', static_url_path='/core-static')

class EmptyForm(FlaskForm):
    pass

def getUserOrAnonymousId():
    if "userid" in session:
        return session["userid"]
    else:
        return "0" # zero indicates anonymous user

def getUserOrAnonymousName():
    if "username" in session:
        return session["username"]
    else:
        return "Anonymous"

class NewBookForm(FlaskForm):
    booktitle = StringField("booktitle")
    link1 = StringField("link1")
    link2 = StringField("link2")
    filepdf = FileField("filepdf")

class EditBookForm(FlaskForm):
    booktitle = StringField("booktitle")
    link1 = StringField("link1")
    link2 = StringField("link2")
    filepdf = FileField("filepdf")

class NewReviewBookForm(FlaskForm):
    reviewtext = StringField("reviewtext")

def getNewBook(userid):
    form = NewBookForm()
    return render_template("new-book.html", form=form)

def getNewReviewBook(userid, book, reviewtext, message=None):
    form = NewReviewBookForm()
    booktitle = book["booktitle"]
    bookid = book["bookid"]
    maxlength = config.REVIEW_MAX_LEN

    return render_template("new-review-book.html", message=message, reviewtext=reviewtext, maxlength=maxlength, form=form, booktitle=booktitle, bookid=bookid)

def getEditBook(userid, book, message=None):
    form = EditBookForm()
    booktitle = book["booktitle"]
    link1 = book["link1"]
    link2 = book["link2"]
    bookid = book["bookid"]
    return render_template("edit-book.html", form=form, bookid=bookid, booktitle=booktitle, link1=link1, link2=link2, message=message)


ALLOWED_EXTENSIONS = ["pdf"]
# https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
def allowed_file(filename):
    return True
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def checkBookPost(form):
    if not form.validate_on_submit():
        abort(500)

    if "filepdf" not in request.files:
        abort(500)

    file = request.files['filepdf']
    if file.filename == "":
        return ["You do not attach a file."] #return [render_template(template, bookid=bookid, form=form, message="You do not attach a file.")]
    if not allowed_file(file):
        return ["Your file must be a PDF."] #return [render_template(template, bookid=bookid, form=form, message="Your file must be a PDF.")]

    filepdf = request.files['filepdf'].read()

    if len(filepdf) > config.MAX_PDF_SIZE:
        return ["Your file is too large."] #return [render_template(template, bookid=bookid, form=form, message="Your file is too large.")]

    try:
        smallpages = convert_from_bytes(filepdf, config.SMALL_DPI, fmt="jpg")
        largepages = convert_from_bytes(filepdf, config.LARGE_DPI, fmt="jpg")
    except exceptions.PDFPageCountError:
        return ["Your file must be a PDF"] #return [render_template(template, bookid=bookid, form=form, message="Your file must be a PDF")]

    if len(smallpages) < 1 or len(smallpages) > config.MAX_PDF_PAGES:
        return [f"Your PDF exceeds {config.MAX_PDF_PAGES} pages"] #return [render_template(template, bookid=bookid, form=form, message=f"Your PDF exceeds {config.MAX_PDF_PAGES} pages")]


    smallbytes = []
    largebytes = []
    for page in smallpages:
        img_byte_arr = BytesIO()
        page.save(img_byte_arr, format='jpeg')
        img_byte_arr = img_byte_arr.getvalue()
        smallbytes.append(img_byte_arr)
    for page in largepages:
        img_byte_arr = BytesIO()
        page.save(img_byte_arr, format='jpeg')
        img_byte_arr = img_byte_arr.getvalue()
        largebytes.append(img_byte_arr)
        
        #with BytesIO() as output:
            #page.save(output, 'jpg')
            #data = output.getvalue()
            #smallbytes.append(data)

    # TODO: validate dimensions of each page
    #for page in pages:
        #if page

    #else:
        # TODO: better friendly error message on missing file, and not PDF filetype
    #    abort(500)

    booktitle = form.data["booktitle"]
    link1 = form.data["link1"]
    link2 = form.data["link2"]

    if not config.saneBooktitle(booktitle):
        return ["Invalid book title"] #return [render_template(template, bookid=bookid, form=form, message="Invalid book title")]
    if not config.saneLinkUrl(link1):
        return ["Invalid primary link url"] #return [render_template(template, bookid=bookid, form=form, message="Invalid primary link url")]
    if not config.saneLinkUrl(link2):
        return ["Invalid secondary link url"] #return [render_template(template, bookid=bookid, form=form, message="Invalid secondary link url")]
    if len(link1) == 0:
        return ["You must include a primary link."] #return [render_template(template, bookid=bookid, form=form, message="You must include a primary link.")]

    return [booktitle, link1, link2, smallbytes, largebytes]
        

def postNewBook(userid):
    form = NewBookForm()

    result = checkBookPost(form)
    if len(result) == 1:
        message = result[0]
        return render_template("new-book.html", bookid=bookid, form=form, message=message)
    
    [booktitle, link1, link2, smallbytes, largebytes] = result
    
    bookid = db.insertNewBook(userid, booktitle, link1, link2, smallbytes, largebytes)

    return redirect(url_for('core_gomden_blueprint.existingbook', bookid=bookid))

def postNewReviewBook(userid, book):
    form = NewReviewBookForm()

    if not form.validate_on_submit():
        abort(500)



    reviewtext = form.data["reviewtext"]

    if len(reviewtext) == 0 or len(reviewtext) > config.REVIEW_MAX_LEN:
        return getNewReviewBook(userid, book, reviewtext, message="Your review is empty")

    db.insertNewReviewBook(userid, bookid=book["bookid"], reviewtext=reviewtext)

    bookid = book["bookid"]

    # Make sure to do perms
    return redirect(url_for('core_gomden_blueprint.existing_review_book',bookid=bookid))
    #return render_template("view-review-book.html", message=None, reviewtext=reviewtext, maxlength=maxlength, form=form, booktitle=booktitle, bookid=bookid)

def reviewToParas(reviewtext):
    return list(filter(lambda x: not re.match(r"^\s+$", x), re.split(r"(\s*\n\s*)(\s*\n\s*)+",  reviewtext)))

@core_gomden_blueprint.route('/club-members-only/private/myreviews')
def myreviews():
    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    reviews = db.getMyReviews(userid)
    reviews = [revRecToParas(r) for r in reviews]

    form = EmptyForm()

    return render_template("my-reviews.html", form=form, reviews=reviews)

@core_gomden_blueprint.route('/club-members-only/private/mypoints')
def mypoints():
    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    points = db.calcPoints(userid)

    numBooks = points["numBooks"]
    numReviews = points["numReviews"]
    numTotalBooks = points["numTotalBooks"]
    numTotalReviews = points["numTotalReviews"]

    form = EmptyForm()

    return render_template("my-points.html", form=form, numBooks=numBooks, numReviews=numReviews, numTotalBooks=numTotalBooks, numTotalReviews=numTotalReviews)

    


# For reviewers to see their own reviews
@core_gomden_blueprint.route('/club-members-only/private/myreview/<int:bookid>')
def existing_review_book(bookid):

    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    book = db.getBook(bookid)

    if book == None:
        abort(403)

    # You cannot review your own book
    if book["userid"] == userid:
        abort(403)

    reviewtext = db.getReview(userid, bookid)

    if reviewtext == None:
        abort(403)

    bookid = book["bookid"]
    booktitle = book["booktitle"]

    # Split into paragraphs
    paras = reviewToParas(reviewtext)


    form = EmptyForm()

    return render_template("my-existing-review.html", bookid=bookid, booktitle=booktitle, paras=paras, form=form)





def postEditBook(userid, book):
    form = NewBookForm()

    bookid = book["bookid"]

    result = checkBookPost(form)
    if len(result) == 1:
        message = result[0]
        return getEditBook(userid, book, message)

    [booktitle, link1, link2, smallbytes, largebytes] = result
    
    db.updateBook(bookid, userid, booktitle, link1, link2, smallbytes, largebytes)

    return redirect(url_for('core_gomden_blueprint.existingbook', bookid=bookid))

@core_gomden_blueprint.route("/club-members-only/private/edit-book/<int:bookid>", methods=["GET", "POST"])
def edit_book(bookid):
    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    book = db.getBook(bookid)

    if book == None:
        abort(404)

    if book["userid"] != userid:
        abort(403)

    if book["bookid"] != bookid:
        abort(403)

    if request.method == "GET":
        return getEditBook(userid, book)
    else:
        return postEditBook(userid, book)


@core_gomden_blueprint.route("/club-members-only/private/review-book/<int:bookid>", methods=["GET", "POST"])
def review_book(bookid):
    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    book = db.getBook(bookid)

    if book == None:
        abort(404)

    # You cannot review your own book
    if book["userid"] == userid:
        abort(403)

    # TODO: if you've already reviewed this book

    reviewtext = db.getReview(userid, bookid)

    if reviewtext != None:
         reviewtext = reviewtext[:config.REVIEW_MAX_LEN]
    else:
         reviewtext = ""

    if request.method == "GET":
        return getNewReviewBook(userid, book, reviewtext)
    else:
        return postNewReviewBook(userid, book)

class MyBooksForm(FlaskForm):
    bookid = StringField("bookid")

@core_gomden_blueprint.route("/club-members-only/private/mybooks", methods=["GET", "POST"])
def mybooks():
    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    if request.method == "GET":
        return getMybooks(userid)
    else:
        return postMybooks(userid)

def postMybooks(userid):

    form = MyBooksForm()

    if "add-sig" in request.form:
        # passes userid of visitor
        db.addSig(userid,request.form["add-sig"])
    elif "remove-sig" in request.form:
        db.removeSig(userid, request.form["remove-sig"])
    else:
        abort(500)

    return redirect(url_for('core_gomden_blueprint.mybooks'))
    

def getMybooks(userid):


    form = MyBooksForm()


    (displayname, sigbookid, sigbooktitle, books) = db.getMyBooks(userid)

    user = db.getConfirmedUserByUserid(userid)

    return render_template("mybooks.html", form=form, books=books, user=user, displayname=displayname, sigbookid=sigbookid, sigbooktitle=sigbooktitle)



@core_gomden_blueprint.route("/club-members-only/private/new-book", methods=["GET", "POST"])
def newbook():
    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    if request.method == "GET":
        return getNewBook(userid)
    else:
        return postNewBook(userid)

def oldtob64(img):
    im_file = BytesIO()
    img.save(im_file, format="JPEG")
    im_bytes = im_file.getvalue()  # im_bytes: image in binary format.
    im_b64 = base64.b64encode(im_bytes)
    return str(im_b64)

#.decode('ascii')

 # img = Image.open(image_path).convert('RGB')
def tob64(page):
    buffered = BytesIO()
    page.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('ascii')
    return img_str

def revRecToParas(rec):
    rec["paras"] = reviewToParas(rec["reviewtext"])
    return rec


@core_gomden_blueprint.route("/public/book/<int:bookid>", methods=["GET"])
def publicbookpage(bookid):
    form = EmptyForm()

    book = db.getBook(bookid)

    if book == None:
        abort(404)

    reviews = db.getPublicReviews(book["bookid"])
    reviews = [revRecToParas(r) for r in reviews]

    links = [book["link1"]]

    numpdfpages = 1

    edit = False
    review = None

    return render_template("public-book-page.html", sigbookid=book["sigbookid"], sigbooktitle=book["sigbooktitle"], displayname=book["displayname"], reviews=reviews, form=form, edit=edit, bookid=book["bookid"], booktitle=book["booktitle"], links=links, numpdfpages=numpdfpages, review=review)


# TODO: separate into ./private/.
@core_gomden_blueprint.route("/club-members-only/private/mybook/<bookid>", methods=["GET", "POST"])
def myexistingbook(bookid):

    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    if request.method == "GET":
        return getExistingBook(userid, bookid, shared=False)
    else:
        return postExistingBook(userid, bookid)

@core_gomden_blueprint.route("/club-members-only/shared/book/<bookid>", methods=["GET"])
def existingbook(bookid):

    if "userid" not in session:
        abort(403)

    userid = session["userid"]
    
    #return getExistingBook(userid, bookid, shared=True)
    return redirect(url_for('core_gomden_blueprint.publicbookpage', bookid=bookid))

class ExistingBookForm(FlaskForm):
    bookid = StringField("bookid")

# TODO: ddd make sure book owner matches visitor
def postExistingBook(userid, bookid):
    form = ExistingBookForm()

    if "make-public" in request.form:
        # passes userid of visitor
        db.makeReviewPublicPrivate(userid, bookid, request.form["make-public"], True)
    elif "make-private" in request.form:
        db.makeReviewPublicPrivate(userid, bookid, request.form["make-private"], False)
    else:
        abort(500)

    return redirect(url_for('core_gomden_blueprint.myexistingbook', bookid=bookid))
    
def getExistingBook(userid, bookid, shared):

    form = ExistingBookForm()

    book = db.getBook(bookid)

    if book == None:
        abort(404)

    if userid == book["userid"]:
        reviews = db.getAllReviews(book["bookid"])
        reviews = [revRecToParas(r) for r in reviews]
    else:
        reviews = []

    links = [book["link1"]]

    if book["link2"]:
        links.append(book["link2"])

    numpdfpages = book["numpdfpages"]

    edit = (userid == book["userid"]) and not shared
    review = None

    return render_template("book.html", displayname=book["displayname"], sigbookid=book["sigbookid"], sigbooktitle=book["sigbooktitle"], reviews=reviews, form=form, edit=edit, bookid=book["bookid"], booktitle=book["booktitle"], links=links, numpdfpages=numpdfpages, review=review)


@core_gomden_blueprint.route('/club-members-only/shared/page/<int:bookid>/<size>/<int:pagenum>.jpg')
def get_image(bookid, size, pagenum):
    if "userid" not in session:
        abort(403)
    if size == "small":
        size = "SMALL"
    elif size == "large":
        size = "LARGE"
    else:
        abort(404)

    #image_binary = read_image(pid)
    image_binary = db.getImg(bookid, size, pagenum)

    if image_binary == None:
        abort(404)

    return send_file(BytesIO(image_binary),
                     attachment_filename=f'{pagenum}.jpg',
                     mimetype='image/jpg')
    #response = make_response(image_binary)
    #response.headers.set('Content-Type', 'image/jpeg')
    #response.headers.set(
    #    'Content-Disposition', 'attachment', filename='%s.jpg' % pagenum)
    #return response
