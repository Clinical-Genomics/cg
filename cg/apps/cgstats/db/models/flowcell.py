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

    @staticmethod
    def exists(flowcell_name: str) -> Optional[int]:
        """Checks if the Flowcell entry already exists"""
        try:
            flowcell: Flowcell = Flowcell.query.filter_by(flowcellname=flowcell_name).one()
            return flowcell.flowcell_id
        except NoResultFound:
            return None
