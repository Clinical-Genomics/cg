from typing import Optional, Union

from pydantic import BaseModel, validator
from cg.models.report.validators import validate_empty_field, validate_float, validate_gender


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
        bait_set: panel bed used for the analysis; source: LIMS
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

    _bait_set = validator("bait_set", always=True, allow_reuse=True)(validate_empty_field)
    _gender = validator("gender", always=True, allow_reuse=True)(validate_gender)

    _float_values_mip = validator(
        "mapped_reads", "mean_target_coverage", "pct_10x", always=True, allow_reuse=True
    )(validate_float)


class BalsamicSampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample

    Attributes:
            mean_insert_size: mean insert size of the distribution; source: pipeline workflow
            fold_80: fold 80 base penalty; source: pipeline workflow
    """

    mean_insert_size: Union[None, float, str]
    fold_80: Union[None, float, str]

    _float_values_balsamic = validator(
        "mean_insert_size", "fold_80", always=True, allow_reuse=True
    )(validate_float)


class BalsamicTargetedSampleMetadataModel(BalsamicSampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample

    Attributes:
            bait_set: panel bed used for the analysis; source: LIMS
            bait_set_version: panel bed version; source: pipeline workflow
            median_target_coverage: median coverage of a target region in bases; source: pipeline workflow
            pct_250x: percent of targeted bases that are covered to 250X coverage or more; source: pipeline workflow
            pct_500x: percent of targeted bases that are covered to 500X coverage or more; source: pipeline workflow
    """

    bait_set: Optional[str]
    bait_set_version: Union[None, int, str]
    median_target_coverage: Union[None, float, str]
    pct_250x: Union[None, float, str]
    pct_500x: Union[None, float, str]

    _str_values = validator("bait_set", "bait_set_version", always=True, allow_reuse=True)(
        validate_empty_field
    )

    _float_values_balsamic_targeted = validator(
        "median_target_coverage", "pct_250x", "pct_500x", always=True, allow_reuse=True
    )(validate_float)


class BalsamicWGSSampleMetadataModel(BalsamicSampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample

    Attributes:
            median_coverage: median coverage in bases of the genome territory; source: pipeline workflow
            pct_15x: fraction of bases that attained at least 15X sequence coverage; source: pipeline workflow
            pct_60x: fraction of bases that attained at least 15X sequence coverage; source: pipeline workflow
    """

    median_coverage: Union[None, float, str]
    pct_15x: Union[None, float, str]
    pct_60x: Union[None, float, str]

    _float_values_balsamic_wgs = validator(
        "median_coverage", "pct_15x", "pct_60x", always=True, allow_reuse=True
    )(validate_float)
