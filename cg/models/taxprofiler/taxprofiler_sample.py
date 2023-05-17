from cg.constants.sequencing import SequencingPlatform
from cg.models.nextflow.sample import NextflowSample


class TaxprofilerSample(NextflowSample):
    """Taxprofiler sample model

    Attributes:
        instrument_platform: taxprofiler config file attributes model
    """

    instrument_platform: SequencingPlatform
