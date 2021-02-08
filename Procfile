web: gunicorn --worker-class eventlet --no-sendfile --workers=1 gomden:app 
worker: celery -A gomden.celery worker -l info