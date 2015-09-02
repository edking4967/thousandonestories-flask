import os

HEROKU_ENABLED = os.environ.get('HEROKU') is None
