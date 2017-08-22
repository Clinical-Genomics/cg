# -*- coding: utf-8 -*-
import logging

import alchy

from cg.store import models
from .add import AddHandler
from .find import FindHandler
from .status import StatusHandler

log = logging.getLogger(__name__)


class BaseHandler:

    User = models.User
    Customer = models.Customer
    Sample = models.Sample
    Family = models.Family
    FamilySample = models.FamilySample
    Flowcell = models.Flowcell
    Analysis = models.Analysis
    Application = models.Application
    ApplicationVersion = models.ApplicationVersion
    Panel = models.Panel
    Pool = models.Pool
    Delivery = models.Delivery


class CoreHandler(BaseHandler, AddHandler, FindHandler, StatusHandler):
    pass


class Store(alchy.Manager, CoreHandler):

    def __init__(self, uri):
        super(Store, self).__init__(config=dict(SQLALCHEMY_DATABASE_URI=uri), Model=models.Model)
