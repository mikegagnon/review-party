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

def landing_loggedout():
    form = EmptyForm()

    numRegisteredUsers = db.getNumRegisteredUsers()
    form = EmptyForm()
    if numRegisteredUsers == 0:
        return render_template("landing-init.html", form=form)        
    else:
        #return render_template("landing-loggedout.html", form=form)
        #return render_template("account_blueprint.login")
        return redirect(url_for('account_blueprint.login'))


def landing_loggedin():
    form = EmptyForm()
    return render_template("landing-loggedin.html", form=form)

@landing_blueprint.route("/")
def landing():
    form = EmptyForm()

    if "userid" in session:
        return landing_loggedin()
    else:
        return landing_loggedout()
