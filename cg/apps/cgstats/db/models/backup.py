from typing import Optional

from sqlalchemy import Column, ForeignKey, orm, types
from sqlalchemy.orm.exc import NoResultFound

from .backup_tape import Backuptape
from .base import Model


class Backup(Model):
    runname = Column(types.String(255), primary_key=True)
    startdate = Column(types.Date, nullable=False)
    nas = Column(types.String(255))
    nasdir = Column(types.String(255))
    starttonas = Column(types.DateTime)
    endtonas = Column(types.DateTime)
    preproc = Column(types.String(255))
    preprocdir = Column(types.String(255))
    startpreproc = Column(types.DateTime)
    endpreproc = Column(types.DateTime)
    frompreproc = Column(types.DateTime)
    analysis = Column(types.String(255))
    analysisdir = Column(types.String(255))
    toanalysis = Column(types.DateTime)
    fromanalysis = Column(types.DateTime)
    inbackupdir = Column(types.Integer)
    backuptape_id = Column(ForeignKey("backuptape.backuptape_id"), nullable=False)
    backupdone = Column(types.DateTime)
    md5done = Column(types.DateTime)

    tape = orm.relationship("Backuptape", backref=orm.backref("backup"))

    @staticmethod
    def exists(runname: str, tapedir: Optional[str] = None) -> Optional[str]:
        """Check if run is already backed up. Optionally: checks if run is
        on certain tape

        runname (str): e.g. 151117_D00410_0187_AHWYGMADXX
        tapedir (str): the name of the tape, e.g. tape036_037
        """
        try:
            if tapedir is not None:
                backup: Backup = (
                    Backup.query.outerjoin(Backuptape)
                    .filter_by(runname=runname)
                    .filter(Backuptape.tapedir == tapedir)
                    .one()
                )
            else:
                backup: Backup = Backup.query.filter_by(runname=runname).one()
            return backup.runname
        except NoResultFound:
            return None
