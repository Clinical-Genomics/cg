# -*- coding: utf-8 -*-
import logging

import alchy
from cg.store import models
from .add import AddHandler
from .find import FindHandler
from .status import StatusHandler
from .trends import TrendsHandler

LOG = logging.getLogger(__name__)


class CoreHandler(AddHandler, FindHandler, StatusHandler, TrendsHandler):
    pass


class Store(alchy.Manager, CoreHandler):

    def __init__(self, uri):
        self.uri = uri
        super(Store, self).__init__(config=dict(SQLALCHEMY_DATABASE_URI=uri), Model=models.Model)
