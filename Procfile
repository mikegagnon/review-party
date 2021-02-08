web: gunicorn --worker-class=gevent --worker-connections=1000 --no-sendfile --workers=1 gomden:app 
worker: celery -A gomden.celery worker -l info