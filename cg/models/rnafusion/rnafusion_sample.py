from cg.constants.rnafusion import RNAFUSION_ACCEPTED_STRANDEDNESS
from cg.models.nextflow.sample import NextflowSample, validator


class RnafusionSample(NextflowSample):
    """Rnafusion sample model

    Attributes:
        strandedness: rnafusion config file attributes model
    """

    strandedness: str

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("strandedness", always=True)
    def valid_value_strandedness(cls, value) -> str:
        """Verify that the strandedness value is accepted."""
        assert value in RNAFUSION_ACCEPTED_STRANDEDNESS
        return "Strandedness value not valid"
