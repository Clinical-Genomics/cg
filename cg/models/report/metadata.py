from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated

from cg.constants import NA_FIELD
from cg.models.report.validators import (
    get_float_as_percentage,
    get_float_as_string,
    get_gender_as_string,
    get_report_string,
)


class SampleMetadataModel(BaseModel):
    """
    Metrics and trending data model associated to a specific sample.

    Attributes:
        million_read_pairs: number of million read pairs obtained; source: StatusDB/sample/reads (/2*10^6)
        duplicates: fraction of mapped sequence that is marked as duplicate; source: pipeline workflow
    """

    million_read_pairs: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    duplicates: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD


class MipDNASampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to a specific MIP DNA sample.

    Attributes:
        bait_set: panel bed used for the analysis; source: LIMS
        gender: gender estimated by the workflow; source: pipeline workflow
        mapped_reads: percentage of reads aligned to the reference sequence; source: pipeline workflow
        mean_target_coverage: mean coverage of a target region; source: pipeline workflow
        pct_10x: percent of targeted bases that are covered to 10X coverage or more; source: pipeline workflow
    """

    bait_set: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    gender: Annotated[str, BeforeValidator(get_gender_as_string)] = NA_FIELD
    mapped_reads: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    mean_target_coverage: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    pct_10x: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD


class BalsamicSampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample.

    Attributes:
            mean_insert_size: mean insert size of the distribution; source: pipeline workflow
            fold_80: fold 80 base penalty; source: pipeline workflow
    """

    mean_insert_size: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    fold_80: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD


class BalsamicTargetedSampleMetadataModel(BalsamicSampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample.

    Attributes:
            bait_set: panel bed used for the analysis; source: LIMS
            bait_set_version: panel bed version; source: pipeline workflow
            median_target_coverage: median coverage of a target region in bases; source: pipeline workflow
            pct_250x: percent of targeted bases that are covered to 250X coverage or more; source: pipeline workflow
            pct_500x: percent of targeted bases that are covered to 500X coverage or more; source: pipeline workflow
    """

    bait_set: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    bait_set_version: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    median_target_coverage: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    pct_250x: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    pct_500x: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    gc_dropout: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD


class BalsamicWGSSampleMetadataModel(BalsamicSampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample.

    Attributes:
            median_coverage: median coverage in bases of the genome territory; source: pipeline workflow
            pct_15x: fraction of bases that attained at least 15X sequence coverage; source: pipeline workflow
            pct_60x: fraction of bases that attained at least 15X sequence coverage; source: pipeline workflow
    """

    median_coverage: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    pct_15x: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    pct_60x: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    pct_reads_improper_pairs: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD


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

    bias_5_3: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    gc_content: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD
    input_amount: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    insert_size: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    insert_size_peak: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    mapped_reads: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD
    mean_length_r1: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    mrna_bases: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    pct_adapter: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    pct_surviving: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    q20_rate: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD
    q30_rate: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD
    ribosomal_bases: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD
    rin: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
    uniquely_mapped_reads: Annotated[str, BeforeValidator(get_float_as_string)] = NA_FIELD
