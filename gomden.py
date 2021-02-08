import flask
from flask import *
from flask_sslify import SSLify
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from celery import Celery

import json
import time
from urllib.parse import unquote
import random
import string
import os

import config

from core_gomden.core_gomden import core_gomden_blueprint, init as initCore
from landing.landing import landing_blueprint
from account.account import account_blueprint, init as initAccount



app = Flask(__name__, static_url_path="/static")
sslify = SSLify(app)

app.register_blueprint(core_gomden_blueprint)
app.register_blueprint(landing_blueprint)
app.register_blueprint(account_blueprint)

app.config["SECRET_KEY"] = config.SECRET_KEY
# https://stackoverflow.com/questions/41144565/flask-does-not-see-change-in-js-file
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

csrf = CSRFProtect(app)

from flask_mail import  Message
from celery import Celery

celery = Celery(app, broker=config.REDIS_URL)

@app.errorhandler(403)
def forbidden(e):
    # note that we set the 404 status explicitly
    #return render_template('404.html'), 404
    if "userid" in session:
        message = "You are not authorized to view this page."
        return render_template("message.html", message=message), 403
    else:
        message = "Club members only, for this page"
        return render_template("not-logged-in.html", message=message), 403
    


# TODO: rm/simplify print-based logging
@celery.task()
def send_email(subject, sender, recipient, body):
    print("1 Sending email to " + recipient)
    with app.app_context():

        with mail.connect() as connection:
            msg = Message(
                subject,
                sender=sender,
                recipients=[recipient])
            msg.body = body
            print("2 Sending email to " + recipient)
            connection.send(msg)
            print("3 Sending email to " + recipient)

app.config.update(
    MAIL_SERVER=config.FLASK_EMAIL_SERVER,
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=config.NOREPLY_EMAIL,
    MAIL_PASSWORD=config.FLASK_EMAIL_PASSWORD
    )

mail = Mail(app)

initAccount(app, send_email)
initCore(send_email)

