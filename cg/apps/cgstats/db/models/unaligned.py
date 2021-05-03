from typing import Optional

from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.orm.exc import NoResultFound

from .base import Model


class Unaligned(Model):

    unaligned_id = Column(types.Integer, primary_key=True)
    sample_id = Column(ForeignKey("sample.sample_id", ondelete="CASCADE"), nullable=False)
    demux_id = Column(ForeignKey("demux.demux_id", ondelete="CASCADE"), nullable=False)
    lane = Column(types.Integer)
    yield_mb = Column(types.Integer)
    passed_filter_pct = Column(types.Numeric(10, 5))
    readcounts = Column(types.Integer)
    raw_clusters_per_lane_pct = Column(types.Numeric(10, 5))
    perfect_indexreads_pct = Column(types.Numeric(10, 5))
    q30_bases_pct = Column(types.Numeric(10, 5))
    mean_quality_score = Column(types.Numeric(10, 5))
    time = Column(types.DateTime)

    @staticmethod
    def exists(sample_id: int, demux_id: int, lane: int) -> Optional[int]:
        """Checks if an Unaligned entry already exists"""
        try:
            unaligned: Unaligned = (
                Unaligned.query.filter_by(sample_id=sample_id)
                .filter_by(demux_id=demux_id)
                .filter_by(lane=lane)
                .one()
            )
            return unaligned.unaligned_id
        except NoResultFound:
            return None
