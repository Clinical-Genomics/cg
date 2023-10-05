from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated

from cg.models.report.validators import (
    validate_empty_field,
    validate_float,
    validate_gender,
    validate_percentage,
)


class SampleMetadataModel(BaseModel):
    """
    Metrics and trending data model associated to a specific sample.

    Attributes:
        million_read_pairs: number of million read pairs obtained; source: StatusDB/sample/reads (/2*10^6)
        duplicates: fraction of mapped sequence that is marked as duplicate; source: pipeline workflow
    """

    million_read_pairs: Annotated[str, BeforeValidator(validate_float)]
    duplicates: Annotated[str, BeforeValidator(validate_float)]


class MipDNASampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to a specific MIP DNA sample.

    Attributes:
        bait_set: panel bed used for the analysis; source: LIMS
        gender: gender estimated by the pipeline; source: pipeline workflow
        mapped_reads: percentage of reads aligned to the reference sequence; source: pipeline workflow
        mean_target_coverage: mean coverage of a target region; source: pipeline workflow
        pct_10x: percent of targeted bases that are covered to 10X coverage or more; source: pipeline workflow
    """

    bait_set: Annotated[str, BeforeValidator(validate_empty_field)]
    gender: Annotated[str, BeforeValidator(validate_gender)]
    mapped_reads: Annotated[str, BeforeValidator(validate_float)]
    mean_target_coverage: Annotated[str, BeforeValidator(validate_float)]
    pct_10x: Annotated[str, BeforeValidator(validate_float)]


class BalsamicSampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample.

    Attributes:
            mean_insert_size: mean insert size of the distribution; source: pipeline workflow
            fold_80: fold 80 base penalty; source: pipeline workflow
    """

    mean_insert_size: Annotated[str, BeforeValidator(validate_float)]
    fold_80: Annotated[str, BeforeValidator(validate_float)]


class BalsamicTargetedSampleMetadataModel(BalsamicSampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample.

    Attributes:
            bait_set: panel bed used for the analysis; source: LIMS
            bait_set_version: panel bed version; source: pipeline workflow
            median_target_coverage: median coverage of a target region in bases; source: pipeline workflow
            pct_250x: percent of targeted bases that are covered to 250X coverage or more; source: pipeline workflow
            pct_500x: percent of targeted bases that are covered to 500X coverage or more; source: pipeline workflow
    """

    bait_set: Annotated[str, BeforeValidator(validate_empty_field)]
    bait_set_version: Annotated[str, BeforeValidator(validate_empty_field)]
    median_target_coverage: Annotated[str, BeforeValidator(validate_float)]
    pct_250x: Annotated[str, BeforeValidator(validate_float)]
    pct_500x: Annotated[str, BeforeValidator(validate_float)]


class BalsamicWGSSampleMetadataModel(BalsamicSampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample.

    Attributes:
            median_coverage: median coverage in bases of the genome territory; source: pipeline workflow
            pct_15x: fraction of bases that attained at least 15X sequence coverage; source: pipeline workflow
            pct_60x: fraction of bases that attained at least 15X sequence coverage; source: pipeline workflow
    """

    median_coverage: Annotated[str, BeforeValidator(validate_float)]
    pct_15x: Annotated[str, BeforeValidator(validate_float)]
    pct_60x: Annotated[str, BeforeValidator(validate_float)]


class RnafusionSampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to a specific Rnafusion sample.

    Attributes:
        bias_5_3: bias is the ratio between read counts; source: pipeline workflow
        gc_content: percentage of GC bases calculated on trimmed reads; source: pipeline workflow
        input_amount: input amount in ng; source: LIMS
        insert_size: distance between paired-end sequencing reads in a DNA fragment
        insert_size_peak: insert size length; source: pipeline workflow
        mapped_reads: percentage of reads aligned to the reference sequence; source: pipeline workflow
        mean_length_r1: average length of reads that pass QC filters; source: pipeline workflow
        mrna_bases:  proportion of bases that originate from messenger RNA; source: pipeline workflow
        pct_adapter: proportion of reads that contain adapter sequences; source: pipeline workflow
        pct_surviving: percentage of reads that pass quality control filters; source: pipeline workflow
        q20_rate: proportion of bases with a minimum Phred score of 20; source: pipeline workflow
        q30_rate: proportion of bases with a minimum Phred score of 30; source: pipeline workflow
        ribosomal_bases: proportion of bases that originate from ribosomal RNA; source: pipeline workflow
        rin: RNA integrity number; source: LIMS
        uniquely_mapped_reads: percentage of mapped reads; source: pipeline workflow
    """

    bias_5_3: Annotated[str, BeforeValidator(validate_float)]
    gc_content: Annotated[str, BeforeValidator(validate_percentage)]
    input_amount: Annotated[str, BeforeValidator(validate_float)]
    insert_size: Annotated[str, BeforeValidator(validate_float)]
    insert_size_peak: Annotated[str, BeforeValidator(validate_float)]
    mapped_reads: Annotated[str, BeforeValidator(validate_percentage)]
    mean_length_r1: Annotated[str, BeforeValidator(validate_float)]
    mrna_bases: Annotated[str, BeforeValidator(validate_float)]
    pct_adapter: Annotated[str, BeforeValidator(validate_float)]
    pct_surviving: Annotated[str, BeforeValidator(validate_float)]
    q20_rate: Annotated[str, BeforeValidator(validate_percentage)]
    q30_rate: Annotated[str, BeforeValidator(validate_percentage)]
    ribosomal_bases: Annotated[str, BeforeValidator(validate_percentage)]
    rin: Annotated[str, BeforeValidator(validate_float)]
    uniquely_mapped_reads: Annotated[str, BeforeValidator(validate_float)]
