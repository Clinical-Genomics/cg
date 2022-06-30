# -*- coding: utf-8 -*-
import os

# flask
SECRET_KEY = os.environ.get("CG_SECRET_KEY") or "thisIsNotASafeKey"
TEMPLATES_AUTO_RELOAD = True

# sqlalchemy
SQLALCHEMY_DATABASE_URI = os.environ["CG_SQL_DATABASE_URI"]
SQLALCHEMY_POOL_RECYCLE = 7200
SQLALCHEMY_TRACK_MODIFICATIONS = "FLASK_DEBUG" in os.environ

# server
CG_ENABLE_ADMIN = ("FLASK_DEBUG" in os.environ) or (os.environ.get("CG_ENABLE_ADMIN") == "1")

# lims
LIMS_HOST = os.environ["LIMS_HOST"]
LIMS_USERNAME = os.environ["LIMS_USERNAME"]
LIMS_PASSWORD = os.environ["LIMS_PASSWORD"]

OSTICKET_API_KEY = os.environ.get("OSTICKET_API_KEY")
OSTICKET_DOMAIN = os.environ.get("OSTICKET_DOMAIN")
SUPPORT_SYSTEM_EMAIL = os.environ.get("SUPPORT_SYSTEM_EMAIL")
EMAIL_URI = os.environ.get("EMAIL_URI")


# oauth
GOOGLE_OAUTH_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
GOOGLE_OAUTH_CLIENT_SECRET = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]

# invoice
TOTAL_PRICE_TRESHOLD = 750000
