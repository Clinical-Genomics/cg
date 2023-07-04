from sqlalchemy import Column, ForeignKey, types

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
