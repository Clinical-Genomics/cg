from typing import List

from cg.constants.constants import Strandedness
from cg.models.nextflow.sample import NextflowSample


class RnafusionSample(NextflowSample):
    """Rnafusion sample sheet model."""

    sample: str
    fastq_r1: List[str]
    fastq_r2: List[str]
    strandedness: Strandedness
