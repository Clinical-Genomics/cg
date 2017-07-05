# -*- coding: utf-8 -*-
import alchy

from . import models


class BaseHandler:

    User = models.User
    Customer = models.Customer
    Family = models.Family
    Sample = models.Sample
    Flowcell = models.Flowcell
    Analysis = models.Analysis


class Store(alchy.Manager, BaseHandler):

    def __init__(self, uri):
        super(Store, self).__init__(config=dict(SQLALCHEMY_DATABASE_URI=uri), Model=models.Model)
