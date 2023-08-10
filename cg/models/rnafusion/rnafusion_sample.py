from typing import List

from cg.constants.constants import Strandedness
from cg.models.nextflow.sample import NextflowSample, validator


class RnafusionSample(NextflowSample):
    """Rnafusion sample sheet model."""

    sample: str
    fastq_r1: List[str]
    fastq_r2: List[str]
    strandedness: str

    @validator("strandedness", always=True)
    def valid_value_strandedness(cls, value) -> str:
        """Verify that the strandedness value is accepted."""
        assert value in Strandedness.accepted_values()
        return "Strandedness value not valid"
