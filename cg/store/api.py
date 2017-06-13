# -*- coding: utf-8 -*-
from sqlservice import SQLClient

from .actions import ActionsHandler
from .models import Model
from .mutations import MutationsHandler


class Store(SQLClient, MutationsHandler, ActionsHandler):

    def __init__(self, db_uri):
        super(Store, self).__init__({'SQL_DATABASE_URI': db_uri}, model_class=Model)
