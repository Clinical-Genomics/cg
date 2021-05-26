from typing import Optional

from sqlalchemy import Column, types
from sqlalchemy.orm.exc import NoResultFound

from .base import Model


class Backuptape(Model):

    backuptape_id = Column(types.Integer, primary_key=True)
    tapedir = Column(types.String(255))
    nametext = Column(types.String(255))
    tapedate = Column(types.DateTime)

    @staticmethod
    def exists(tapedir: str) -> Optional[int]:
        """Check if a tape already exists
        tapedir (str): the name of the tape, e.g. tape036_037
        """
        try:
            backup_tape: Backuptape = Backuptape.query.filter_by(tapedir=tapedir).one()
            return backup_tape.backuptape_id
        except NoResultFound:
            return None
