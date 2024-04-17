"""This module contains constants for the BCLConvert metrics files."""

from enum import StrEnum


class BclConvertQualityMetricsColumnNames(StrEnum):
    """Column names for the BCLConvert quality metrics file."""

    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "SampleID"
    MEAN_QUALITY_SCORE_Q30: str = "Mean Quality Score (PF)"
    Q30_BASES_PERCENT: str = "% Q30"


class BclConvertDemuxMetricsColumnNames(StrEnum):
    """Column names for the BCLConvert demultiplexing metrics file."""

    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "SampleID"
    READ_PAIR_COUNT: str = "# Reads"


DEMUX_METRICS_FILE_NAME: str = "Demultiplex_Stats.csv"
QUALITY_METRICS_FILE_NAME: str = "Quality_Metrics.csv"
ADAPTER_METRICS_FILE_NAME: str = "Adapter_Metrics.csv"
