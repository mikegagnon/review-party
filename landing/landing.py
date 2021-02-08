import flask
from flask import *
from flask_sslify import SSLify
from flask import Blueprint
from flask_wtf import FlaskForm
import sys
import config
import random

import db

landing_blueprint = Blueprint('landing_blueprint', __name__, template_folder='templates', static_folder="static", static_url_path='/landing-static')

class EmptyForm(FlaskForm):
     pass

# TODO: codedeup wtih account.py
def landing_loggedout(message=None):
    form = EmptyForm()

    numRegisteredUsers = db.getNumRegisteredUsers()
    form = EmptyForm()
    if numRegisteredUsers == 0:
        return render_template("landing-init.html", form=form)        
    else:
        #return render_template("landing-loggedout.html", form=form)
        #return render_template("account_blueprint.login")
        return redirect(url_for('account_blueprint.login', message=message))


# https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunks(lst):
    for i in range(0, len(lst), 3):
        segment = lst[i:i + 3]
        yield segment    

def landing_loggedin():
    form = EmptyForm()

    books = db.getRandomBooks(config.NUM_FRONT_PAGE_BOOKS)

    if len(books) < config.NUM_FRONT_PAGE_BOOKS:
        books += [None] * (config.NUM_FRONT_PAGE_BOOKS - len(books))
        random.shuffle(books)

    return render_template("landing-loggedin.html", form=form, bookchunks=chunks(books))

@landing_blueprint.route("/")
def landing():
    form = EmptyForm()

    if "userid" in session:
        return landing_loggedin()
    else:
        return landing_loggedout()
