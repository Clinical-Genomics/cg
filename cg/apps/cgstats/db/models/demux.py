from typing import Optional

from sqlalchemy import Column, ForeignKey, UniqueConstraint, orm, types
from sqlalchemy.orm.exc import NoResultFound

from .base import Model


class Demux(Model):

    __table_args__ = (UniqueConstraint("flowcell_id", "basemask", name="demux_ibuk_1"),)

    demux_id = Column(types.Integer, primary_key=True)
    flowcell_id = Column(ForeignKey("flowcell.flowcell_id", ondelete="CASCADE"), nullable=False)
    datasource_id = Column(
        ForeignKey("datasource.datasource_id", ondelete="CASCADE"), nullable=False
    )
    basemask = Column(types.String(255))
    time = Column(types.DateTime)

    datasource = orm.relationship("Datasource", cascade="all", backref=orm.backref("demuxes"))
    unaligned = orm.relation(
        "Unaligned", single_parent=True, cascade="all, delete-orphan", backref=orm.backref("demux")
    )
    # add the viewonly attribute to make sure the Session.delete(demux) works
    samples = orm.relation(
        "Sample",
        secondary="unaligned",
        viewonly=True,
        cascade="all",
        backref=orm.backref("demuxes"),
    )

    @staticmethod
    def exists(flowcell_id: int, basemask: str) -> Optional[int]:
        """Checks if the Demux entry already exists"""
        try:
            demux: Demux = (
                Demux.query.filter_by(flowcell_id=flowcell_id).filter_by(basemask=basemask).one()
            )
            return demux.demux_id
        except NoResultFound:
            return None
