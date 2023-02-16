from typing import Optional

from sqlalchemy import Column, ForeignKey, orm, types
from sqlalchemy.orm.exc import NoResultFound

from .base import Model


class Datasource(Model):
    datasource_id = Column(types.Integer, primary_key=True)
    supportparams_id = Column(
        ForeignKey("supportparams.supportparams_id", ondelete="CASCADE"), nullable=False
    )
    runname = Column(types.String(255))
    machine = Column(types.String(255))
    rundate = Column(types.Date)
    document_path = Column(types.String(255), nullable=False)
    document_type = Column(
        types.Enum("html", "xml", "csv", "undefined"), nullable=False, default="html"
    )
    server = Column(types.String(255))
    time = Column(types.DateTime)

    supportparams = orm.relationship(
        "Supportparams", cascade="all", backref=orm.backref("datasources")
    )

    def __repr__(self):
        return "{self.__class__.__name__}: {self.runname}".format(self=self)

    @staticmethod
    def exists(document_path: str) -> Optional[str]:
        """Checks if the Datasource entry already exists"""
        try:
            datasource: Datasource = Datasource.query.filter_by(document_path=document_path).one()
            return datasource.datasource_id
        except NoResultFound:
            return None
