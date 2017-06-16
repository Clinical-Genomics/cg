# -*- coding: utf-8 -*-
import os

SECRET_KEY = "not secure!!"
TEMPLATES_AUTO_RELOAD = True
SQL_DATABASE_URI = os.environ['CG_SQL_DATABASE_URI']
if 'mysql' in SQL_DATABASE_URI:  # pragma: no cover
    SQL_POOL_RECYCLE = 7200
SQLALCHEMY_TRACK_MODIFICATIONS = 'FLASK_DEBUG' in os.environ
