from cg.constants.sequencing import SequencingPlatform
from cg.models.nf_analysis import NextflowSample


class TaxprofilerSample(NextflowSample):
    """Taxprofiler sample model is used when building the sample sheet.

    Attributes:
        instrument_platform: taxprofiler config file attributes model
    """

    instrument_platform: SequencingPlatform
