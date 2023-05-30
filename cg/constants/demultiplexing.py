from pathlib import Path

import click
from cg.utils.enums import StrEnum


class BclConverter(StrEnum):
    """Define the BCL converter."""

    DRAGEN: str = "dragen"
    BCL2FASTQ: str = "bcl2fastq"


class SampleSheetHeaderColumnNames(StrEnum):
    DATA: str = "[Data]"
    FLOW_CELL_ID: str = "FCID"
    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "Sample_ID"
    SAMPLE_NAME: str = "SampleName"
    SAMPLE_PROJECT: str = "Sample_Project"
    CONTROL: str = "Control"


UNKNOWN_REAGENT_KIT_VERSION: str = "unknown"

SAMPLE_SHEET_HEADERS = {
    "bcl2fastq": [
        SampleSheetHeaderColumnNames.FLOW_CELL_ID,
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
        SampleSheetHeaderColumnNames.FLOW_CELL_ID,
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

SAMPLE_SHEET_SETTINGS_HEADER = "[Settings]"

SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX1 = ["BarcodeMismatchesIndex1", "0"]

SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX2 = ["BarcodeMismatchesIndex2", "0"]

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


INDEX_CHECK = "indexcheck"
UNDETERMINED = "Undetermined"

BCL2FASTQ_METRICS_DIRECTORY_NAME = "Stats"
BCL2FASTQ_METRICS_FILE_NAME = "Stats.json"
