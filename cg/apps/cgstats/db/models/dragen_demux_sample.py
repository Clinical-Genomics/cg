"""Get samples with information from Dragen demultiplexing"""


import logging

from pydantic.v1 import BaseModel

LOG = logging.getLogger(__name__)


class DragenDemuxSample(BaseModel):
    """Gather statistics from the Dragen demultiplexing results for a sample"""

    sample_name: str
    flowcell: str
    lane: int
    reads: int = 0
    perfect_reads: int = 0
    one_mismatch_reads: int = 0
    pass_filter_q30: int = 0
    mean_quality_score: float = 0.00
    r1_sample_bases: int = 0
    r2_sample_bases: int = 0
    read_length: int = 0
