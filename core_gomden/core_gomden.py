# PUNT: better logging

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
        return "You do not attach a file"
    if not allowed_file(file):
        return "Your file must be a PDF"   

    filepdf = request.files['filepdf'].read()
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
        return render_template("new-book.html", form=form, message="You must include a primary link")
        
    bookid = db.insertNewBook(userid, booktitle, link1, link2, filepdf)

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


@core_gomden_blueprint.route("/book/<bookid>")
def existingbook(bookid):

    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    form = EmptyForm()

    book = db.getBook(bookid)

    return render_template("book.html", form=form, booktitle=book["booktitle"])

