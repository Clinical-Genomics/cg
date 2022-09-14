from cg.models.nextflow.sample import NextflowSample, validator


class RnafusionSample(NextflowSample):
    """Rnafusion sample model

    Attributes:
        strandedness: balsamic config file attributes model
    """

    strandedness: str

    @validator("strandedness")
    def valid_value_strandedness(cls, value: str):
        assert value in ["reverse", "forward", "unstranded"]
        return value
