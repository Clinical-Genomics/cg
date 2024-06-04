"""This module contains constants for the sequencing and demultiplex metrics files."""

from enum import StrEnum


class QualityMetricsColumnNames(StrEnum):
    """Column names for the quality metrics file."""

    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "SampleID"
    MEAN_QUALITY_SCORE_Q30: str = "Mean Quality Score (PF)"
    QUALITY_SCORE_SUM: str = "QualityScoreSum"
    Q30_BASES_PERCENT: str = "% Q30"
    YIELD: str = "Yield"
    YIELD_Q30: str = "YieldQ30"


class DemuxMetricsColumnNames(StrEnum):
    """Column names for the demultiplexing metrics file."""

    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "SampleID"
    READ_PAIR_COUNT: str = "# Reads"


DEMUX_METRICS_FILE_NAME: str = "Demultiplex_Stats.csv"
QUALITY_METRICS_FILE_NAME: str = "Quality_Metrics.csv"
ADAPTER_METRICS_FILE_NAME: str = "Adapter_Metrics.csv"
