from cg.constants.taxprofiler import TAXPROFILER_ACCEPTED_PLATFORMS
from cg.models.nextflow.sample import NextflowSample, validator


class TaxprofilerSample(NextflowSample):
    """Taxprofiler sample model

    Attributes:
        instrument_platform: taxprofiler config file attributes model
    """

    pass

    # instrument_platform: str

    # @validator("instrument_platform", always=True)
    # def valid_instrument_platform(cls, value) -> str:
    #    """Verify that the instrument platform is accepted."""
    #    assert value in TAXPROFILER_ACCEPTED_PLATFORMS
    #    return "Instrument platform not valid"
