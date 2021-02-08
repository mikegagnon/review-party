import flask
from flask import session, Blueprint, request, render_template, abort, current_app, url_for, redirect
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField
from flask_bcrypt import Bcrypt
from itsdangerous import URLSafeTimedSerializer

from gomden_log import *
import config
import db

def ensureClubMember():
    if "userid" not in session:
        abort(403)
    return session["userid"]

bcrypt = None
send_email = None
def init(app, se):
    global send_email
    global bcrypt
    bcrypt = Bcrypt(app)
    send_email = se

timedSerializer = URLSafeTimedSerializer(config.SECRET_KEY)

account_blueprint = Blueprint('account_blueprint', __name__, template_folder='templates', static_folder='static', static_url_path='/account-static')

class LogoutForm(FlaskForm):
     pass

class EmptyForm(FlaskForm):
    pass

class LoginForm(FlaskForm):
    usernameOrEmail = StringField("UsernameOrEmail")

def pop_session():
    funcname = "pop_session()"
    debug(funcname, "popping session")
    session.pop("userid", None)
    session.pop("displayname", None)
    session.pop("email", None)

class CreateAccountForm(FlaskForm):
    displayname = StringField("DisplayName")
    email = StringField("Email")


@account_blueprint.route("/account/dologin/<token>", methods=["GET"])
def doLogin(token):
    funcname = f'doLogin(token)'

    form = EmptyForm(request.form)

    try:
        [email] = timedSerializer.loads(token, salt="login-link", max_age=config.MAX_LOGIN_TOKEN_AGE)
    except:
        warn(funcname, f"could not extract email from token. Abort 403")
        return render_template("login.html", form=form, message="I'm sorry, but your link has expired.")

    user = db.getConfirmedUserByEmail(email)
    if not user:
        abort(500)

    if db.hasTokenBeenUsed(token):
        return render_template("login.html", form=form, message="I'm sorry, your login link has already been used. Try again.")
    else:
        db.markTokenUsed(token)

    session["userid"] = user["userid"]
    session["displayname"] = user["displayname"]
    session["email"] = email

    info(funcname, "login success")
    return redirect(url_for('landing_blueprint.landing'))



def sendLoginLinkEmail(email):
    # https://itsdangerous.palletsprojects.com/en/1.1.x/serializer/#the-salt
    token = timedSerializer.dumps([email], salt="login-link")

    confirm_url = url_for(
        "account_blueprint.doLogin",
        token=token,
        _external=True)

    subject = f"{config.DOMAIN}: login link"
    sender = config.NOREPLY_EMAIL
    recipient = email
    body = f"{confirm_url} this link will expire in an hour."

    send_email.delay(subject, sender, recipient, body)

def getInviteLink(userid):
    token = timedSerializer.dumps([userid], salt="invite-link")

    invitelink = url_for(
        "account_blueprint.create_account",
        token=token,
        _external=True)

    return invitelink

def getWorkToInvite(userid):
    numreviews = len(db.getMyReviews(userid))
    numbooks = len(db.getMyBooks(userid))
    if numreviews == 0 and numbooks == 0:
        return "I'm sorry, but before you can invite a friend, you must post a book, and post a review."
    if numreviews == 0:
        return "I'm sorry, but before you can invite a friend, you must post a review."
    if numbooks == 0:
        return "I'm sorry, but before you can invite a friend, you must post a book."
    return None


@account_blueprint.route("/club-members-only/invite", methods=["GET"])
def invitepage():
    userid = ensureClubMember()

    form = EmptyForm(request.form)

    # let the admin (userid = 1) skip the work
    if config.WORK_BEFORE_INVITE and userid != 1:
        message = getWorkToInvite(userid)
        if message != None:
            return render_template("message.html", form=form, message=message)

    userid = session["userid"]
    invitelink = getInviteLink(userid)
    return render_template("invite.html", form=form, invitelink=invitelink)

def sendConfirmationEmail(email):
    # https://itsdangerous.palletsprojects.com/en/1.1.x/serializer/#the-salt
    token = timedSerializer.dumps([email], salt="email-account-confirmation")

    confirm_url = url_for(
        "account_blueprint.confirm_email",
        token=token,
        _external=True)

    subject = f"{config.DOMAIN}: please confirm your email"
    sender = config.NOREPLY_EMAIL
    recipient = email
    body = (f"Follow this link to confirm your new account with {config.DOMAIN}: " +
            confirm_url)

    send_email.delay(subject, sender, recipient, body)

# ctodo
def sendCannotCreateAccount(email):
    subject = f"{config.DOMAIN}: Cannot create account"
    sender = config.NOREPLY_EMAIL
    recipient = email
    body = (f"You (or someone else), attempted to register a new account with your email address. Did you forget your username or password? If so, follow this link to reset your password for {config.DOMAIN}: " + url_for("account_blueprint.forgot", _external=True))
    send_email.delay(subject, sender, recipient, body)

def sendNewRegisteredEmailToAdmin(email):
    subject = f"{config.DOMAIN} new user registered"
    sender = config.NOREPLY_EMAIL
    recipient = config.ADMIN_EMAIL
    body = f"A new user registered: @{email}"
    send_email.delay(subject, sender, recipient, body)
    
class MyMultipleConfirmedAccounts(Exception):
    pass

def getConfirmedFromUsers(users):
    user = list(filter(lambda x: x["setup_state"] == "EMAIL_CONFIRMED", users))
    if len(user) == 1:
        return user[0]
    elif len(user) == 0:
        return None
    else:
        raise MyMultipleConfirmedAccounts

class ShouldNotContainConfirmedUser(Exception):
    pass

def getUnconfirmedUsersForMatchingEmailFromUsers(users):
    # Just to double check there's no confirmed users
    user = getConfirmedFromUsers(users)

    if user:
        raise ShouldNotContainConfirmedUser

    return list(filter(lambda x: x["email"] == email, users))


class MultipleUnconfirmedUsernamesForSameEmailAddress(Exception):
    pass

def getUnconfirmedUserByEmailFromUsers(email, users):
     #Just to double check there's no confirmed users
     user = getConfirmedFromUsers(users)
     if user:
         raise ShouldNotContainConfirmedUser

     user = list(filter(lambda x: x["email"] == email, users))

     if len(user) == 1:
         return user[0]
     elif len(user) == 0:
         return None
     else:
         raise MultipleUnconfirmedUsernamesForSameEmailAddress

@account_blueprint.route("/account/create/<token>", methods=["GET", "POST"])
def create_account(token):
    funcname = "create_account()"

    form = CreateAccountForm(request.form)

    numRegisteredUsers = db.getNumRegisteredUsers()
    #form = EmptyForm()
    if numRegisteredUsers == 0:
        referUserid = 0
    else:
        try:
            [referUserid] = timedSerializer.loads(token, salt="invite-link", max_age=config.MAX_INVITE_TOKEN_AGE)
        except:
            error(funcname, f"could not extract referUserid from token. Abort 404")
            abort(404)

    if "userid" in session:
        debug(funcname, 'Already logged in')
        return render_template("already_loggedin.html", form=form)

    if request.method == "GET":
        debug(funcname, 'request.method == "GET"')
        return render_template("create-account.html", invitetoken=token, form=form, message=None)
    
    if not form.validate_on_submit():
        error(funcname, 'not form.validate_on_submit()')
        abort(403)

    displayname = config.trimDisplayName(form.displayname.data)
    email = form.email.data

    if not config.saneDisplayName(displayname):
        debug(funcname, 'not saneDisplayName(displayname)')
        return render_template("create-account.html", invitetoken=token, form=form, message="Invalid display name.")

    if not config.saneEmail(email):
        debug(funcname, 'not saneEmail(email)')
        return render_template("create-account.html", invitetoken=token, form=form, message="Invalid email address.")

    # NOTE: there can be multiple __unconfirmed__ accounts with the same email
    # address, because someone who doesn't own the email might register accounts
    # for that email. However, there can only be one __confirmed__ account
    # per email address

    try:
        users = db.getAllUsersForAnySetupStateByEmail(email)
    except db.ShouldBeImpossible:
        critcal(funcname, "Should be impossible from db.getAllUsersForAnySetupStateByEmail for email: %s" % email)
        abort(500)
    except db.MultipleConfirmedAccounts:
        critcal(funcname, "Multiple confirmed accounts for email in db: %s" % email)
        abort(500)

    try:
        confirmedUser = getConfirmedFromUsers(users)
    except MyMultipleConfirmedAccounts:
        critcal(funcname, "Multiple confirmed accounts for email: %s" % email)
        abort(500)

    # If this email already has a confirmed account
    if confirmedUser:
        # this email address is aleady confirmed
        sendCannotCreateAccount(email)
        return render_template("create-account-success.html", form=form, email=email)

    # If this email address is not confirmed
    else:
        # We know this email address is not confirmed
        try:
            usersWithEmail = getUnconfirmedUsersForMatchingEmailFromUsers(users)
        except ShouldNotContainConfirmedUser:
            critcal(funcname, "ShouldNotContainConfirmedUser while calling getUnconfirmedUsersForMatchingEmailFromUsers")
            abort(500)
        
        try:
            user = getUnconfirmedUserByEmailFromUsers(email, users)
        except MultipleUnconfirmedUsernamesForSameEmailAddress:
            critcal(funcname, "MultipleUnconfirmedUsernamesForSameEmailAddress")
            abort(500)

        # If it's the case that that this email has an
        # unconfirmed account, then just re-send the confirmation email
        if user:
            # We know: username is not taken, and this email address is not confirmed,
            # and this username pair has already attempted account creation.
            # So, just re-send a confirmation email.
            sendConfirmationEmail(email)

            return render_template("create-account-success.html", form=form, email=email)
        # If this email-username pair does not have a record in the database
        else:

            if db.hasTokenBeenUsed(token):
                return render_template("message.html", message="I'm sorry, your invite link has expired")
            else:
                db.markTokenUsed(token)

            # We know: username is not taken, and this email address is not confirmed,
            # and we know this uername-email pair does not have a record in the db.
            # So, add a new record to the database
            db.createUnconfirmedAccount(displayname, email, referUserid)
            sendConfirmationEmail(email)

            return render_template("create-account-success.html", form=form, email=email)

@account_blueprint.route("/account/confirm-email/<token>", methods=["GET"])
def confirm_email(token):
    funcname = f'confirm_email(token)'

    form = EmptyForm(request.form)

    try:
        [email] = timedSerializer.loads(token, salt="email-account-confirmation", max_age=config.MAX_TOKEN_AGE)
    except:
        error(funcname, f"could not extract email from token. Abort 404")
        abort(404)

    user = db.getConfirmedUserByEmail(email)
    if user:
        # If the applicant has already registered this username/email pair
        if user["email"] == email:
            return render_template("message.html", form=form, message="You have already confirmed your account for email %s." % email)
        # If someone else swooped in and registered this username
        else:
            return render_template("message.html", form=form, message="Sorry! Someone else registered the email %s while we were waiting for you to click the confirmation link." % email)

    user = db.getUnconfirmedUserByEmail(email)
    if not user:
        critcal(funcname, "Could not find email: %s" % email)
        abort(500)

    try:
        db.confirmEmail(email)
    except db.ConfirmUsernameEmailErrorRowCountNotOne:
        critcal(funcname, "ConfirmUsernameEmailErrorRowCountNotOne")
        abort(500)

    session["userid"] = user["userid"]
    session["displayname"] = user["displayname"]
    session["email"] = email

    info(funcname, f"sending email to admin")
    sendNewRegisteredEmailToAdmin(email)

    info(funcname, "success")
    return render_template("message.html", form=form, message="You have confirmed your account. You are now logged in.")

@account_blueprint.route("/account/logout", methods=["GET", "POST"])
def logout():
    ensureClubMember()

    funcname = "logout()"

    form = EmptyForm(request.form)

    if "userid" not in session:
        return render_template("message.html", form=form, message="You are already logged out.")

    if request.method == "GET":
        return render_template("logout.html", form=form)

    if not form.validate_on_submit():
        abort(403)

    pop_session()
    return render_template("message.html", form=form, message="You are now logged out.")


@account_blueprint.route("/account/login", methods=["GET", "POST"])
def login():
    funcname = "login()"

    form = LoginForm(request.form)

    if "userid" in session:
        debug(funcname, '"userid" in session')
        return render_template("already_loggedin.html", form=form)

    if request.method == "GET":
        debug(funcname, 'request.method == "GET"')
        return render_template("login.html", form=form, message=None)

    if not form.validate_on_submit():
        error(funcname, 'not form.validate_on_submit()')
        abort(403)

    email = form.usernameOrEmail.data

    if not config.saneEmail(email):
        info(funcname, "something isn't sane")
        return render_template("login.html", form=form, message=config.BAD_EMAIL_MESSAGE)

    user = db.getConfirmedUserByEmail(email)

    if not user:
        info(funcname, "not user")
        return render_template("sending-link.html", form=form, message=config.SENDING_LOGIN_LINK_MESSAGE)
    else:
        sendLoginLinkEmail(email)
        return render_template("sending-link.html", form=form, message=config.SENDING_LOGIN_LINK_MESSAGE)

class ResetPasswordForm(FlaskForm):
    password1 = PasswordField("Password1")
    password2 = PasswordField("Password2")
