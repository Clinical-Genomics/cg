# -*- coding: utf-8 -*-
from sqlalchemy import types, Column
from sqlservice import declarative_base

Model = declarative_base()


class Base:
    id = Column(types.Integer, primary_key=True)
