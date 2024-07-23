from pydantic import BaseModel, BeforeValidator, field_validator
from typing_extensions import Annotated

from cg.constants import NA_FIELD, RIN_MAX_THRESHOLD, RIN_MIN_THRESHOLD
from cg.models.report.validators import (
    get_float_as_percentage,
    get_initial_qc_as_string,
    get_number_as_string,
    get_report_string,
    get_sex_as_string,
)


class SampleMetadataModel(BaseModel):
    """
    Metrics and trending data model associated to a specific sample.

    Attributes:
        duplicates: fraction of mapped sequence that is marked as duplicate; source: workflow
        million_read_pairs: number of million read pairs obtained; source: StatusDB/sample/reads (/2*10^6)
        initial_qc: initial QC protocol flag; source: LIMS
    """

    duplicates: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    million_read_pairs: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    initial_qc: Annotated[str, BeforeValidator(get_initial_qc_as_string)] = NA_FIELD


class MipDNASampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to a specific MIP DNA sample.

    Attributes:
        bait_set: panel bed used for the analysis; source: LIMS
        gender: gender estimated by the workflow; source: workflow
        mapped_reads: percentage of reads aligned to the reference sequence; source: workflow
        mean_target_coverage: mean coverage of a target region; source: workflow
        pct_10x: percent of targeted bases that are covered to 10X coverage or more; source: workflow
    """

    bait_set: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    gender: Annotated[str, BeforeValidator(get_sex_as_string)] = NA_FIELD
    mapped_reads: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    mean_target_coverage: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    pct_10x: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD


class BalsamicSampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample.

    Attributes:
        mean_insert_size: mean insert size of the distribution; source: workflow
        fold_80: fold 80 base penalty; source: workflow
    """

    mean_insert_size: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    fold_80: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD


class BalsamicTargetedSampleMetadataModel(BalsamicSampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample.

    Attributes:
        bait_set: panel bed used for the analysis; source: LIMS
        bait_set_version: panel bed version; source: workflow
        median_target_coverage: median coverage of a target region in bases; source: workflow
        pct_250x: percent of targeted bases that are covered to 250X coverage or more; source: workflow
        pct_500x: percent of targeted bases that are covered to 500X coverage or more; source: workflow
    """

    bait_set: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    bait_set_version: Annotated[str, BeforeValidator(get_report_string)] = NA_FIELD
    gc_dropout: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    median_target_coverage: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    pct_250x: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    pct_500x: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD


class BalsamicWGSSampleMetadataModel(BalsamicSampleMetadataModel):
    """Metrics and trending data model associated to a specific BALSAMIC sample.

    Attributes:
        median_coverage: median coverage in bases of the genome territory; source: workflow
        pct_15x: fraction of bases that attained at least 15X sequence coverage; source: workflow
        pct_60x: fraction of bases that attained at least 15X sequence coverage; source: workflow
        pct_reads_improper_pairs: fraction of reads that are not properly aligned in pairs
    """

    median_coverage: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    pct_15x: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    pct_60x: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    pct_reads_improper_pairs: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD


class SequencingSampleMetadataModel(SampleMetadataModel):
    """Metrics and trending data model associated to the sequencing of a sample."

    Attributes:
        gc_content: percentage of GC bases calculated on trimmed reads; source: workflow
        mean_length_r1: average length of reads that pass QC filters; source: workflow
    """

    gc_content: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD
    mean_length_r1: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD


class WTSSampleMetadataModel(SequencingSampleMetadataModel):
    """Metrics and trending data model associated to a WTS sample.

    Attributes:
        bias_5_3: bias is the ratio between read counts; source: workflow
        dv200: percentage of RNA fragments > 200 nucleotides; source: LIMS
        input_amount: input amount in ng; source: LIMS
        mrna_bases:  proportion of bases that originate from messenger RNA; source: workflow
        pct_adapter: proportion of reads that contain adapter sequences; source: workflow
        pct_surviving: percentage of reads that pass quality control filters; source: workflow
        q20_rate: proportion of bases with a minimum Phred score of 20; source: workflow
        q30_rate: proportion of bases with a minimum Phred score of 30; source: workflow
        ribosomal_bases: proportion of bases that originate from ribosomal RNA; source: workflow
        rin: RNA integrity number; source: LIMS
        uniquely_mapped_reads: percentage of mapped reads; source: workflow
    """

    bias_5_3: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    dv200: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    input_amount: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    mrna_bases: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    pct_adapter: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    pct_surviving: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    q20_rate: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD
    q30_rate: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD
    ribosomal_bases: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD
    rin: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    uniquely_mapped_reads: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD

    @field_validator("rin")
    def ensure_rin_thresholds(cls, rin: str) -> str:
        if rin != NA_FIELD:
            rin_number = float(rin)
            if RIN_MIN_THRESHOLD <= rin_number <= RIN_MAX_THRESHOLD:
                return str(rin_number)
        return NA_FIELD


class RnafusionSampleMetadataModel(WTSSampleMetadataModel):
    """Metrics and trending data model associated to a specific Rnafusion sample.

    Attributes:
        insert_size: distance between paired-end sequencing reads in a DNA fragment
        insert_size_peak: insert size length; source: workflow
        mapped_reads: percentage of reads aligned to the reference sequence; source: workflow
    """

    insert_size: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    insert_size_peak: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    mapped_reads: Annotated[str, BeforeValidator(get_float_as_percentage)] = NA_FIELD


class TaxprofilerSampleMetadataModel(SequencingSampleMetadataModel):
    """Metrics and trending data model associated to a Taxprofiler sample.

    Attributes:
        average_read_length: average length of reads; source: workflow
        mapped_reads: reads aligned to the reference sequence; source: workflow
        mean_length_r2: average length of reads for read2; source: workflow
        million_read_pairs_after_filtering: number of reads after filtering; source: workflow
    """

    average_read_length: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    mapped_reads: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    mean_length_r2: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    million_read_pairs_after_filtering: Annotated[str, BeforeValidator(get_number_as_string)] = (
        NA_FIELD
    )


class TomteSampleMetadataModel(WTSSampleMetadataModel):
    """Metrics and trending data model associated to a Tomte sample.

    Attributes:
        pct_intergenic_bases: proportion of genomic bases located between genes; source: workflow
        pct_intronic_bases: proportion of genomic bases within intronic regions; source: workflow
    """

    pct_intergenic_bases: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
    pct_intronic_bases: Annotated[str, BeforeValidator(get_number_as_string)] = NA_FIELD
