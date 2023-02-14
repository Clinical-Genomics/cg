from typing import Optional

from sqlalchemy import Column, ForeignKey, orm, types
from sqlalchemy.orm.exc import NoResultFound

from .base import Model


class Sample(Model):
    sample_id = Column(types.Integer, primary_key=True)
    project_id = Column(ForeignKey("project.project_id", ondelete="CASCADE"), nullable=False)
    samplename = Column(types.String(255), nullable=False)
    customerid = Column(types.String(255))
    limsid = Column(types.String(255))
    barcode = Column(types.String(255))
    time = Column(types.DateTime)

    unaligned = orm.relationship(
        "Unaligned", cascade="all, delete-orphan", backref=orm.backref("sample")
    )

    @property
    def lims_id(self) -> str:
        """Parse out the LIMS id from the sample name in demux database."""
        sample_part = self.samplename.split("_")[0]
        return sample_part.rstrip("FB")

    @staticmethod
    def exists(sample_name: str, barcode: str) -> Optional[int]:
        """Checks if a Sample entry already exists"""
        try:
            sample: Sample = (
                Sample.query.filter_by(samplename=sample_name).filter_by(barcode=barcode).one()
            )
            return sample.sample_id
        except NoResultFound:
            return None
