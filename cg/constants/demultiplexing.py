"""Constants related to demultiplexing."""
from pathlib import Path
from typing import List, Dict
import click
from cg.utils.enums import Enum, StrEnum


class BclConverter(StrEnum):
    """Define the BCL converter."""

    DRAGEN: str = "dragen"
    BCL2FASTQ: str = "bcl2fastq"
    BCLCONVERT: str = "bcl_convert"


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


class SampleSheetNovaSeq6000Sections:
    """Class with all necessary constants for building a NovaSeqX sample sheet."""

    class Settings(StrEnum):
        HEADER: str = "[Settings]"
        BARCODE_MISMATCH_INDEX1: str = "BarcodeMismatchesIndex1, 0"
        BARCODE_MISMATCH_INDEX2: str = "BarcodeMismatchesIndex2, 0"

    class Data(Enum):
        HEADER: str = "[Data]"
        FLOW_CELL_ID: str = "FCID"
        LANE: str = "Lane"
        SAMPLE_INTERNAL_ID_BCL2FASTQ: str = "SampleID"
        SAMPLE_INTERNAL_ID_BCLCONVERT: str = "Sample_ID"
        SAMPLE_NAME: str = "SampleName"
        SAMPLE_PROJECT_BCL2FASTQ: str = "Project"
        SAMPLE_PROJECT_BCLCONVERT: str = "Sample_Project"
        CONTROL: str = "Control"

        COLUMN_NAMES: Dict[str, List[str]] = {
            "bcl2fastq": [
                FLOW_CELL_ID,
                LANE,
                SAMPLE_INTERNAL_ID_BCL2FASTQ,
                "SampleRef",
                "index",
                "index2",
                SAMPLE_NAME,
                CONTROL,
                "Recipe",
                "Operator",
                SAMPLE_PROJECT_BCL2FASTQ,
            ],
            "dragen": [
                FLOW_CELL_ID,
                LANE,
                SAMPLE_INTERNAL_ID_BCLCONVERT,
                "SampleRef",
                "index",
                "index2",
                SAMPLE_NAME,
                CONTROL,
                "Recipe",
                "Operator",
                SAMPLE_PROJECT_BCLCONVERT,
            ],
        }


class SampleSheetNovaSeqXSections:
    """Class with all necessary constants for building a NovaSeqX sample sheet."""

    class Header(StrEnum):
        HEADER: str = "[Header]"
        FILE_FORMAT: str = "FileFormatVersion, 2"
        RUN_NAME: str = "RunName, "
        INSTRUMENT_PLATFORM: str = "InstrumentPlatform, NovaSeqXSeries"
        INDEX_ORIENTATION_FORWARD: str = "IndexOrientation, Forward"

    class Reads(StrEnum):
        HEADER: str = "[Reads]"
        READ_CYCLES_1: str = "Read1Cycles, "
        READ_CYCLES_2: str = "Read2Cycles, "
        INDEX_CYCLES_1: str = "Index1Cycles, "
        INDEX_CYCLES_2: str = "Index2Cycles, "

    class Settings(StrEnum):
        HEADER: str = "[BCLConvert_Settings]"
        SOFTWARE_VERSION: str = "SoftwareVersion, 4.1.5"
        FASTQ_COMPRESSION_FORMAT: str = "FastqCompressionFormat, gzip"

    class Data(Enum):
        HEADER: str = "[BCLConvert_Data]"
        COLUMN_NAMES: List[str] = [
            "Lane",
            "Sample_ID",
            "Index",
            "Index2",
            "AdapterRead1",
            "AdapterRead2",
            "BarcodeMismatchesIndex1",
            "BarcodeMismatchesIndex2",
        ]


OPTION_BCL_CONVERTER = click.option(
    "-b",
    "--bcl-converter",
    type=click.Choice(["bcl2fastq", "dragen"]),
    default="bcl2fastq",
    help="Specify bcl conversion software. Choose between bcl2fastq and dragen. Default is "
    "bcl2fastq.",
)


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

BCL2FASTQ_METRICS_DIRECTORY_NAME = "Stats"
BCL2FASTQ_METRICS_FILE_NAME = "Stats.json"
DRAGEN_PASSED_FILTER_PCT = 100.00000
FASTQ_FILE_SUFFIXES = [".fastq", ".gz"]
INDEX_CHECK = "indexcheck"
UNDETERMINED = "Undetermined"
