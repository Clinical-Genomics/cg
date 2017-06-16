# -*- coding: utf-8 -*-
from flask_cors import CORS
from flask_sqlservice import FlaskSQLService

from cg.store import models
from cg.store.actions import ActionsHandler
from cg.store.mutations import MutationsHandler


class CgFlaskSqlservice(FlaskSQLService, ActionsHandler, MutationsHandler):
    pass


db = CgFlaskSqlservice(model_class=models.Model)
cors = CORS(resources={r"/api/*": {"origins": "*"}})
