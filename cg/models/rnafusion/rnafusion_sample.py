from pydantic import field_validator

from cg.constants.rnafusion import RNAFUSION_ACCEPTED_STRANDEDNESS
from cg.models.nextflow.sample import NextflowSample


class RnafusionSample(NextflowSample):
    """Rnafusion sample model

    Attributes:
        strandedness: rnafusion config file attributes model
    """

    strandedness: str

    @field_validator("strandedness")
    def valid_value_strandedness(cls, value) -> str:
        """Verify that the strandedness value is accepted."""
        assert value in RNAFUSION_ACCEPTED_STRANDEDNESS
        return "Strandedness value not valid"
