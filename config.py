import re
import os

# ZTODO rm
GUEST_CODE = "foo"
GUEST_IMG = None
GUEST_IMG_BACKUP = None

SECRET_KEY = os.environ["SECRET_KEY"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
NOREPLY_EMAIL = os.environ["NOREPLY_EMAIL"] 
DOMAIN = os.environ["STYLED_DOMAIN_NAME"]
FLASK_EMAIL_SERVER = os.environ["FLASK_EMAIL_SERVER"]
FLASK_EMAIL_PASSWORD = os.environ["FLASK_EMAIL_PASSWORD"]
REDIS_URL = os.environ["REDIS_URL"]

SMALL_DPI = 100
LARGE_DPI = 100 # dups small, since whatever
MAX_PDF_SIZE = 20 * 1000 * 1000 # 20 MB
MAX_PDF_PAGES = 10 # page count
MAX_PDF_WIDTH = 12  #in inches
MAX_PDF_HEIGHT = 12 #in inches

NUM_FRONT_PAGE_BOOKS = 6

REVIEW_MAX_LEN = 1000

# ZTODO rm
CODE_LEN = 3

MIN_USERNAME_LEN = 3
MAX_USERNAME_LEN = 15

MIN_DISPLAYNAME_LEN = 1
MAX_DISPLAYNAME_LEN = 30

USERNAME_RE = re.compile(r"^[a-z][a-z0-9\-]+$", re.UNICODE)

MIN_EMAIL_LEN = 5
MAX_EMAIL_LEN = 254

MIN_PASSWORD_LEN = 3
MAX_PASSWORD_LEN = 64

MIN_BOOKTITLE_LEN = 1
MAX_BOOKTITLE_LEN = 100

MIN_LINK_URL_LEN = 10
MAX_LINK_URL_LEN = 300

# https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
LINKURL_RE = re.compile(r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$", re.UNICODE)

MAX_TOKEN_AGE = 86400 # 24 hours
MAX_LOGIN_TOKEN_AGE = 3600 # 1 hour
MAX_INVITE_TOKEN_AGE = 86400 # 24 hours

DUMMY_HASH="$2b$12$iqrN79syuOte2ZHdDASDF.ASDF."

BAD_EMAIL_MESSAGE = """Your email seems invalid."""
SENDING_LOGIN_LINK_MESSAGE = """Sending you a link to login."""
FORGOT_PASSWORD_MESSAGE = """Check your email for a link to reset your password. But, if you haven't yet created and confirmed your account (via the confirmation-link email), you will not receive an email."""

def saneBooktitle(booktitle):
    return (
        len(booktitle) >= MIN_BOOKTITLE_LEN and
        len(booktitle) <= MAX_BOOKTITLE_LEN
    )

def saneLinkUrl(link):
    return len(link) == 0 or (
        len(link) >= MIN_LINK_URL_LEN and
        len(link) <= MAX_LINK_URL_LEN and
        LINKURL_RE.match(link)
    )

def saneUsername(username):
    return (
        len(username) >= MIN_USERNAME_LEN and
        len(username) <= MAX_USERNAME_LEN and
        USERNAME_RE.match(username)
    )

def trimDisplayName(displayname):
    displayname = displayname.strip()
    displayname = re.sub(r"\s\s+", " ", displayname)
    return displayname


def saneDisplayName(displayname):
    return (
        len(displayname) >= MIN_DISPLAYNAME_LEN and
        len(displayname) <= MAX_DISPLAYNAME_LEN
    )

def saneEmail(email):
    return (
        len(email) >= MIN_EMAIL_LEN and
        len(email) <= MAX_EMAIL_LEN
    )

# TODO regex for sanePasswords
def sanePassword(password):
    return (
        len(password) >= MIN_PASSWORD_LEN and
        len(password) <= MAX_PASSWORD_LEN
    )

MIN_DOCNAME_LEN = 1
MAX_DOCNAME_LEN = 500

def saneDocname(docname):
    return (
        len(docname) >= MIN_DOCNAME_LEN and
        len(docname) <= MAX_DOCNAME_LEN
    )

MIN_TOPIC_LEN = 1
MAX_TOPIC_LEN = 500
def saneTopic(topic):
    return (
        len(topic) >= MIN_TOPIC_LEN and
        len(topic) <= MAX_TOPIC_LEN
    )

MIN_SUBJECT_LEN = 1
MAX_SUBJECT_LEN = 100
def saneSubject(subject):
    return (
        len(subject) >= MIN_SUBJECT_LEN and
        len(subject) <= MAX_SUBJECT_LEN
    )

PAGENAME_RE = re.compile(r"^[a-z0-9\-]+$", re.UNICODE)
MIN_PAGENAME_LEN = 3
MAX_PAGENAME_LEN = 100

def sanePagename(pagename):
    if len(pagename) < MIN_PAGENAME_LEN or len(pagename) > MAX_PAGENAME_LEN:
        return False
    if not PAGENAME_RE.match(pagename):
        return False
    return True

MAX_CONTENT_LEN = 1000000
def saneContent(content):
    return len(content) <= MAX_CONTENT_LEN
