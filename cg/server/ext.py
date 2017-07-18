# -*- coding: utf-8 -*-
from flask_admin import Admin
from flask_alchy import Alchy
from flask_cors import CORS

from cg.store import models, api


class CgAlchy(Alchy, api.CoreHandler):
    pass


cors = CORS(resources={r"/api/*": {'origins': '*'}}, supports_credentials=True)
db = CgAlchy(Model=models.Model)
admin = Admin(name='Clinical Genomics')
