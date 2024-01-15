"""This module contains constants for the BCLConvert metrics files."""

from enum import StrEnum

from cg.constants.demultiplexing import (
    BclConverter,
    SampleSheetBcl2FastqSections,
    SampleSheetBCLConvertSections,
)


class BclConvertQualityMetricsColumnNames(StrEnum):
    """Column names for the BCLConvert quality metrics file."""

    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "SampleID"
    MEAN_QUALITY_SCORE_Q30: str = "Mean Quality Score (PF)"
    Q30_BASES_PERCENT: str = "% Q30"


SAMPLE_SHEET_HEADER: dict[str, str] = {
    BclConverter.BCL2FASTQ: ",".join(
        [
            column
            for column in SampleSheetBcl2FastqSections.Data.column_names()
            if column != "index2"
        ]
    ),
    BclConverter.BCLCONVERT: ",".join(
        [
            column
            for column in SampleSheetBCLConvertSections.Data.column_names()
            if column != "index2"
        ]
    ),
}


class BclConvertDemuxMetricsColumnNames(StrEnum):
    """Column names for the BCLConvert demultiplexing metrics file."""

    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "SampleID"
    READ_PAIR_COUNT: str = "# Reads"


DEMUX_METRICS_FILE_NAME: str = "Demultiplex_Stats.csv"
QUALITY_METRICS_FILE_NAME: str = "Quality_Metrics.csv"
ADAPTER_METRICS_FILE_NAME: str = "Adapter_Metrics.csv"
