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

def postNewBook(userid):
    form = NewBookForm()

    #form = PhotoForm()
    if form.validate_on_submit():
        filepdf = request.files['filepdf'].read()
    else:
        abort(500)

    booktitle = form.data.booktitle
    link1 = form.data.link1
    link2 = form.data.link2

    if not config.saneBooktitle(booktitle):
        return render_template("new-book.html", form=form, message="Invalid book title")
    if not config.saneLinkUrl(link1):
        return render_template("new-book.html", form=form, message="Invalid primary link url")
    if not config.saneLinkUrl(link2):
        return render_template("new-book.html", form=form, message="Invalid secondary link url")

    bookid = db.insertNewBook(userid, booktitle, link1, link2, filepdf)

    return render_template('book.html', form=form, bookid=id)


@core_gomden_blueprint.route("/new-book", methods=["GET", "POST"])
def newbook():
    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    if request.method == "GET":
        return getNewBook(userid)
    else:
        return postNewBook(userid)


@core_gomden_blueprint.route("/new-book")
def existingbook():

    if "userid" not in session:
        abort(403)

    userid = session["userid"]

    abort(403)

