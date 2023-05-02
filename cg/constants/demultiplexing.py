from pathlib import Path

import click
from cgmodels.cg.constants import StrEnum


class BclConverter(StrEnum):
    DRAGEN: str = "dragen"
    BCL2FASTQ: str = "bcl2fastq"


SEQUENCING_INSTRUMENTS_NAMES = {
    "NovaSeq6000": ["A00621", "A00187", "A00689", "A01901"],
    "NovaSeqX": ["LH00188"],
}

SAMPLE_SHEET_DATA_COLUMNS = {
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

SAMPLE_SHEET_HEADER = "[Header]"
SAMPLE_SHEET_HEADER_FILE_FORMAT_V1 = "FileFormatVersion,1"
SAMPLE_SHEET_HEADER_FILE_FORMAT_V2 = "FileFormatVersion,2"
SAMPLE_SHEET_HEADER_INSTRUMENT_TYPE_NOVASEQX = "InstrumentType,NovaSeqX"
SAMPLE_SHEET_HEADER_INSTRUMENT_PLATFORM = "InstrumentPlatform,NovaSeqXSeries"
SAMPLE_SHEET_HEADER_INDEX_ORIENTATION = "IndexOrientation,Forward"

SAMPLE_SHEET_READS_HEADER = "[Reads]"

SAMPLE_SHEET_SETTINGS_HEADER = {"bcl2fastq": "[Settings]", "dragen": "[BCLConvert_Settings]"}
SAMPLE_SHEET_SETTINGS_SOFTWARE_VERSION = "SoftwareVersion,4.1.5"
SAMPLE_SHEET_SETTINGS_FASTQ_FORMAT = "FastqCompressionFormat,gzip"
SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX1 = "BarcodeMismatchesIndex1,0"
SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX2 = "BarcodeMismatchesIndex2,0"

SAMPLE_SHEET_DATA_HEADER = {"bcl2fastq": "[Data]", "dragen": "[BCLConvert_Data]"}

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
