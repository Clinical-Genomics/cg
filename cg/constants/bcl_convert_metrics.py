"""This module contains constants for the BCLConvert metrics files."""

from enum import Enum
from pathlib import Path


class BclConvertQualityMetricsColumnNames(Enum):
    """Column names for the BCLConvert quality metrics file."""

    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "SampleID"
    READ_PAIR_NUMBER: str = "ReadNumber"
    YIELD_BASES: str = "Yield"
    YIELD_Q30: str = "YieldQ30"
    QUALITY_SCORE_SUM: str = "QualityScoreSum"
    MEAN_QUALITY_SCORE_Q30: str = "Mean Quality Score (PF)"
    Q30_BASES_PERCENT: str = "% Q30"


class BclConvertDemuxMetricsColumnNames(Enum):
    """Column names for the BCLConvert demultiplexing metrics file."""

    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "SampleID"
    SAMPLE_PROJECT: str = "Sample_Project"
    READ_PAIR_COUNT: str = "# Reads"
    PERFECT_INDEX_READS_COUNT: str = "# Perfect Index Reads"
    PERFECT_INDEX_READS_PERCENT: str = "% Perfect Index Reads"
    ONE_MISMATCH_INDEX_READS_COUNT: str = "# One Mismatch Index Reads"
    TWO_MISMATCH_INDEX_READS_COUNT: str = "# Two Mismatch Index Reads"


class BclConvertAdapterMetricsColumnNames(Enum):
    """Column names for the BCLConvert adapter metrics file."""

    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "Sample_ID"
    SAMPLE_PROJECT: str = "Sample_Project"
    READ_NUMBER: str = "ReadNumber"
    SAMPLE_BASES: str = "SampleBases"


DEMUX_METRICS_FILE_NAME = "Demultiplex_Stats.csv"
QUALITY_METRICS_FILE_NAME = "Quality_Metrics.csv"
ADAPTER_METRICS_FILE_NAME = "Adapter_Metrics.csv"
SAMPLE_SHEET_FILE_NAME = "SampleSheet.csv"
