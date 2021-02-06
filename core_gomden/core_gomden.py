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

def getNewBook(userid):

    form = NewBookForm()
    return render_template("new-book.html", form=form)

ALLOWED_EXTENSIONS = ["pdf"]
# https://flask.palletsprojects.com/en/1.1.x/patterns/fileuploads/
def allowed_file(filename):
    return True
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def postNewBook(userid):
    form = NewBookForm()

    if not form.validate_on_submit():
        abort(500)

    if "filepdf" not in request.files:
        abort(500)

    file = request.files['filepdf']
    if file.filename == "":
        return render_template("new-book.html", form=form, message="You do not attach a file.")
    if not allowed_file(file):
        return render_template("new-book.html", form=form, message="Your file must be a PDF.")

    filepdf = request.files['filepdf'].read()

    if len(filepdf) > config.MAX_PDF_SIZE:
        return render_template("new-book.html", form=form, message="Your file is too large.")

    try:
        smallpages = convert_from_bytes(filepdf, config.SMALL_DPI, fmt="jpg")
        largepages = convert_from_bytes(filepdf, config.LARGE_DPI, fmt="jpg")
    except exceptions.PDFPageCountError:
        return render_template("new-book.html", form=form, message="Your file must be a PDF")

    if len(smallpages) < 1 or len(smallpages) > config.MAX_PDF_PAGES:
        return render_template("new-book.html", form=form, message=f"Your PDF exceeds {config.MAX_PDF_PAGES} pages")


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
        return render_template("new-book.html", form=form, message="Invalid book title")
    if not config.saneLinkUrl(link1):
        return render_template("new-book.html", form=form, message="Invalid primary link url")
    if not config.saneLinkUrl(link2):
        return render_template("new-book.html", form=form, message="Invalid secondary link url")
    if len(link1) == 0:
        return render_template("new-book.html", form=form, message="You must include a primary link.")
        
    bookid = db.insertNewBook(userid, booktitle, link1, link2, smallbytes, largebytes)

    return redirect(url_for('core_gomden_blueprint.existingbook', bookid=bookid))

    #render_template('book.html', form=form, bookid=id)


@core_gomden_blueprint.route("/new-book", methods=["GET", "POST"])
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

@core_gomden_blueprint.route("/book/<bookid>")
def existingbook(bookid):

    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    form = EmptyForm()

    book = db.getBook(bookid)

    return book["booktitle"]

    #bits = book["bits"]

    #pages = convert_from_bytes(bits, 200, fmt="jpg")

    #page = pages[0]

    img = tob64(page)
    return render_template("book.html", form=form, booktitle=book["booktitle"], img=img)


@core_gomden_blueprint.route('/page/<int:bookid>/<size>/<int:pagenum>.jpg')
def get_image(bookid, size, pagenum):

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
