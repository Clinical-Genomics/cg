from cg.models.nextflow.sample import NextflowSample, validator
from cg.constants.constants import RNAFUSION_ACCEPTED_STRANDEDNESS


class RnafusionSample(NextflowSample):
    """Rnafusion sample model

    Attributes:
        strandedness: rnafusion config file attributes model
    """

    strandedness: str

    @validator("strandedness", always=True)
    def valid_value_strandedness(cls, value) -> str:
        assert value in RNAFUSION_ACCEPTED_STRANDEDNESS
        return "Strandedness value not valid"
