from pathlib import Path

import click
from cg.utils.enums import StrEnum


class BclConverter(StrEnum):
    """Define the BCL converter."""

    DRAGEN: str = "dragen"
    BCL2FASTQ: str = "bcl2fastq"
    BCLCONVERT: str = "bcl_convert"


class RunParametersXMLNodes(StrEnum):
    """Define names of the used XML nodes in run parameters files."""

    # Node names
    APPLICATION: str = ".Application"
    APPLICATION_VERSION: str = ".ApplicationVersion"
    CYCLES: str = "Cycles"
    INDEX_1_NOVASEQ_6000: str = "./IndexRead1NumberOfCycles"
    INDEX_2_NOVASEQ_6000: str = "./IndexRead2NumberOfCycles"
    INDEX_1_NOVASEQ_X: str = "Index1"
    INDEX_2_NOVASEQ_X: str = "Index2"
    INNER_READ: str = ".//Read"
    INSTRUMENT_TYPE: str = ".InstrumentType"
    PLANNED_READS: str = "./PlannedReads"
    READ_1_NOVASEQ_6000: str = "./Read1NumberOfCycles"
    READ_2_NOVASEQ_6000: str = "./Read2NumberOfCycles"
    READ_1_NOVASEQ_X: str = "Read1"
    READ_2_NOVASEQ_X: str = "Read2"
    READ_NAME: str = "ReadName"
    REAGENT_KIT_VERSION: str = "./RfidsInfo/SbsConsumableVersion"

    # Node Values
    NOVASEQ_6000_APPLICATION: str = "NovaSeq Control Software"
    NOVASEQ_X_INSTRUMENT: str = "NovaSeqXPlus"
    UNKNOWN_REAGENT_KIT_VERSION: str = "unknown"


class SampleSheetHeaderColumnNames(StrEnum):
    DATA: str = "[Data]"
    FLOW_CELL_ID: str = "FCID"
    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "Sample_ID"
    SAMPLE_NAME: str = "SampleName"
    SAMPLE_PROJECT: str = "Sample_Project"
    CONTROL: str = "Control"


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
    BCL2FASTQ_TILE_DIR_PATTERN: str = r"l\dt\d{2}"


INDEX_CHECK = "indexcheck"
UNDETERMINED = "Undetermined"

BCL2FASTQ_METRICS_DIRECTORY_NAME = "Stats"
BCL2FASTQ_METRICS_FILE_NAME = "Stats.json"
