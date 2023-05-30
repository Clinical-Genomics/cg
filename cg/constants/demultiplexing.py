from pathlib import Path

import click
from typing import List, Dict
from cg.constants.sequencing import Sequencers
from cg.utils.enums import StrEnum


class BclConverter(StrEnum):
    """Define the BCL converter."""

    DRAGEN: str = "dragen"
    BCL2FASTQ: str = "bcl2fastq"


class SampleSheetV1Sections:
    """Class that groups all constants to build a sample sheet v1."""

    class Data(StrEnum):
        HEADER: str = "[Data]"
        FLOW_CELL_ID: str = "FCID"

    DATA_COLUMN_NAMES: Dict[str, List[str]] = {
        "bcl2fastq": [
            Data.FLOW_CELL_ID.value,
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
            Data.FLOW_CELL_ID.value,
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


class SampleSheetSections:
    """Class that groups all constants to build a sample sheet v2."""

    INSTRUMENT_PLATFORMS: Dict[str, str] = {
        Sequencers.NOVASEQ.value: "NovaSeq6000Series",
        Sequencers.NOVASEQX.value: "NovaSeqXSeries",
    }

    class Header(StrEnum):
        HEADER: str = "[Header]"
        FILE_FORMAT: List[str] = ["FileFormatVersion", "2"]
        RUN_NAME: str = "RunName, "
        INSTRUMENT_PLATFORM: List[str] = "InstrumentPlatform, "
        INDEX_ORIENTATION_FORWARD: List[str] = ["IndexOrientation", "forward"]

    class Reads(StrEnum):
        HEADER: str = "[Reads]"
        READ_CYCLES_1: str = "Read1Cycles"
        READ_CYCLES_2: str = "Read2Cycles"
        INDEX_CYCLES_1: str = "Index1Cycles"
        INDEX_CYCLES_2: str = "Index2Cycles"

    class Settings(StrEnum):
        HEADER: str = "[BCLConvert_Settings]"
        SOFTWARE_VERSION: List[str] = ["SoftwareVersion", "4.1.5"]
        FASTQ_COMPRESSION_FORMAT: List[str] = ["FastqCompressionFormat", "gzip"]

    class Data(StrEnum):
        HEADER: str = "[BCLConvert_Data]"
        COLUMN_NAMES: List[str] = [
            "Lane",
            "Sample_ID",
            "Index",
            "Index2",
            "OverrideCycles",
            "AdapterRead1",
            "AdapterRead2",
            "BarcodeMismatchesIndex1",
            "BarcodeMismatchesIndex2",
        ]


class SampleSheetHeaderColumnNames(StrEnum):
    DATA: str = "[Data]"
    FLOW_CELL_ID: str = "FCID"
    LANE: str = "Lane"
    SAMPLE_INTERNAL_ID: str = "Sample_ID"
    SAMPLE_NAME: str = "SampleName"
    SAMPLE_PROJECT: str = "Sample_Project"
    CONTROL: str = "Control"


UNKNOWN_REAGENT_KIT_VERSION: str = "unknown"

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
