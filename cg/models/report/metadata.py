from typing import Optional, Union

from pydantic import BaseModel, validator
from cg.models.report.validators import validate_empty_field, validate_float


class SampleMetadataModel(BaseModel):
    """
    Metrics and trending data model associated to a specific sample

    Attributes:
        million_read_pairs: number of million read pairs obtained; source: StatusDB/sample/reads (/2*10^6)
        duplicates: fraction of mapped sequence that is marked as duplicate; source: pipeline workflow

    """

    million_read_pairs: Union[None, float, str]
    duplicates: Union[None, float, str]

    _float_values = validator("million_read_pairs", "duplicates", always=True, allow_reuse=True)(
        validate_float
    )


class MipDNASampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to a specific MIP DNA sample

    Attributes:
        bait_set: panel bed used for the analysis; StatusDB/sample/capture_kit
        gender: gender estimated by the pipeline; source: pipeline workflow
        mapped_reads: percentage of reads aligned to the reference sequence; source: pipeline workflow
        mean_target_coverage: mean coverage of a target region; source: pipeline workflow
        pct_10x: percent of targeted bases that are covered to 10X coverage or more; source: pipeline workflow
    """

    bait_set: Optional[str]
    gender: Optional[str]
    mapped_reads: Union[None, float, str]
    mean_target_coverage: Union[None, float, str]
    pct_10x: Union[None, float, str]

    _str_values_mip = validator("bait_set", "gender", always=True, allow_reuse=True)(
        validate_empty_field
    )

    _float_values_mip = validator(
        "mapped_reads", "mean_target_coverage", "pct_10x", always=True, allow_reuse=True
    )(validate_float)
