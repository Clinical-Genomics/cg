from typing import Optional

from sqlalchemy import Column, types
from sqlalchemy.orm.exc import NoResultFound

from .base import Model


class Supportparams(Model):
    supportparams_id = Column(types.Integer, primary_key=True)
    document_path = Column(types.String(255), nullable=False, unique=True)
    systempid = Column(types.String(255))
    systemos = Column(types.String(255))
    systemperlv = Column(types.String(255))
    systemperlexe = Column(types.String(255))
    idstring = Column(types.String(255))
    program = Column(types.String(255))
    commandline = Column(types.Text)
    sampleconfig_path = Column(types.String(255))
    sampleconfig = Column(types.Text(16777215))
    time = Column(types.DateTime)

    def __repr__(self):
        return "{self.__class__.__name__}: {self.document_path}".format(self=self)

    @staticmethod
    def exists(document_path: str) -> Optional[int]:
        """Checks if the supportparams entry already exists"""
        try:
            support_params: Supportparams = Supportparams.query.filter_by(
                document_path=document_path
            ).one()
            return support_params.supportparams_id
        except NoResultFound:
            return None
