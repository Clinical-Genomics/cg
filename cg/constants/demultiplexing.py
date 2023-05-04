from pathlib import Path

import click
from typing import List
from cgmodels.cg.constants import StrEnum


class BclConverter(StrEnum):
    """Define the BCL converter."""

    DRAGEN: str = "dragen"
    BCL2FASTQ: str = "bcl2fastq"


class FlowCellType(StrEnum):
    """Define the flow cell type."""

    NOVASEQ: str = "novaseq"
    HISEQ: str = "hiseq"


class SequencingInstruments(StrEnum):
    """Define properties of the sequencing instruments."""

    NOVASEQXPLUS: str = "NovaSeqXPlus"
    NOVASEQ6000: str = "NovaSeq6000"
    NOVA_SEQ_6000_NAMES: List[str] = ["A00621", "A00187", "A00689", "A01901"]
    NOVA_SEQ_X_PLUS_NAMES: str = ["LH00188"]


UNKNOWN_REAGENT_KIT_VERSION: str = "unknown"

SAMPLE_SHEET_HEADERS = {
    "bcl2fastq": [
        "FCID",
        "Lane",
        "SampleID",
        "SampleRef",
        "index",
        "index2",
        "SampleName",
        "Control",
        "Recipe",
        "Operator",
        "Project",
    ],
    "dragen": [
        "FCID",
        "Lane",
        "Sample_ID",
        "SampleRef",
        "index",
        "index2",
        "SampleName",
        "Control",
        "Recipe",
        "Operator",
        "Sample_Project",
    ],
}

SAMPLE_SHEET_DATA_HEADER = "[Data]"

SAMPLE_SHEET_SETTINGS_HEADER = "[Settings]"

SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX1 = "BarcodeMismatchesIndex1,0"

SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX2 = "BarcodeMismatchesIndex2,0"

OPTION_BCL_CONVERTER = click.option(
    "-b",
    "--bcl-converter",
    type=click.Choice(["bcl2fastq", "dragen"]),
    default="bcl2fastq",
    help="Specify bcl conversion software. Choose between bcl2fastq and dragen. Default is "
    "bcl2fastq.",
)

FASTQ_FILE_SUFFIXES = [".fastq", ".gz"]

DEMUX_STATS_PATH = {
    "bcl2fastq": {
        "demultiplexing_stats": Path("Stats", "DemultiplexingStats.xml"),
        "conversion_stats": Path("Stats", "ConversionStats.xml"),
        "runinfo": None,
    },
    "dragen": {
        "demultiplexing_stats": Path("Reports", "Demultiplex_Stats.csv"),
        "conversion_stats": Path("Reports", "Demultiplex_Stats.csv"),
        "adapter_metrics_stats": Path("Reports", "Adapter_Metrics.csv"),
        "runinfo": Path("Reports", "RunInfo.xml"),
        "quality_metrics": Path("Reports", "Quality_Metrics.csv"),
    },
}

DRAGEN_PASSED_FILTER_PCT = 100.00000


class DemultiplexingDirsAndFiles(StrEnum):
    """Demultiplexing related directories and files."""

    COPY_COMPLETE: str = "CopyComplete.txt"
    DELIVERY: str = "delivery.txt"
    DEMUX_STARTED: str = "demuxstarted.txt"
    DEMUX_COMPLETE: str = "demuxcomplete.txt"
    Hiseq_X_COPY_COMPLETE: str = "copycomplete.txt"
    HiseqX_TILE_DIR: str = "l1t11"
    RTACOMPLETE: str = "RTAComplete.txt"
    RUN_PARAMETERS: str = "RunParameters.xml"
    SAMPLE_SHEET_FILE_NAME: str = "SampleSheet.csv"
    UNALIGNED_DIR_NAME: str = "Unaligned"
