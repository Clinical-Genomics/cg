from typing import Optional

from sqlalchemy import Column, orm, types
from sqlalchemy.orm.exc import NoResultFound

from .base import Model


class Flowcell(Model):
    flowcell_id = Column(types.Integer, primary_key=True)
    flowcellname = Column(types.String(255), nullable=False, unique=True)
    flowcell_pos = Column(types.Enum("A", "B"), nullable=False)
    hiseqtype = Column(types.String(255), nullable=False)
    time = Column(types.DateTime)

    demux = orm.relationship("Demux", cascade="all", backref=orm.backref("flowcell"))
