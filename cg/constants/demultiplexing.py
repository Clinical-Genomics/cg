"""Constants related to demultiplexing."""
from enum import Enum, StrEnum
from pathlib import Path

import click

from cg.constants.sequencing import Sequencers


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
    HISEQ_X_COPY_COMPLETE: str = "copycomplete.txt"
    HISEQ_X_TILE_DIR: str = "l1t11"
    RTACOMPLETE: str = "RTAComplete.txt"
    RUN_PARAMETERS_PASCAL_CASE: str = "RunParameters.xml"
    RUN_PARAMETERS_CAMEL_CASE: str = "runParameters.xml"
    SAMPLE_SHEET_FILE_NAME: str = "SampleSheet.csv"
    UNALIGNED_DIR_NAME: str = "Unaligned"
    BCL2FASTQ_TILE_DIR_PATTERN: str = r"l\dt\d{2}"
    QUEUED_FOR_POST_PROCESSING: str = "post_processing_queued.txt"
    ANALYSIS_COMPLETED: str = "Secondary_Analysis_Complete.txt"
    ANALYSIS: str = "Analysis"
    DATA: str = "Data"
    BCL_CONVERT: str = "BCLConvert"
    FLOW_CELLS_DIRECTORY_NAME: str = "flow_cells"
    DEMULTIPLEXED_RUNS_DIRECTORY_NAME: str = "demultiplexed_runs"
    ILLUMINA_FILE_MANIFEST: str = "Manifest.tsv"
    CG_FILE_MANIFEST: str = "file_manifest.tsv"
    INTER_OP: str = "InterOp"


class RunParametersXMLNodes(StrEnum):
    """Define names of the used XML nodes in run parameters files."""

    # Node names
    APPLICATION: str = ".Application"
    APPLICATION_NAME: str = ".//ApplicationName"
    APPLICATION_VERSION: str = ".ApplicationVersion"
    CYCLES: str = "Cycles"
    INDEX_1_HISEQ: str = ".//IndexRead1"
    INDEX_2_HISEQ: str = ".//IndexRead2"
    INDEX_1_NOVASEQ_6000: str = "./IndexRead1NumberOfCycles"
    INDEX_2_NOVASEQ_6000: str = "./IndexRead2NumberOfCycles"
    INDEX_1_NOVASEQ_X: str = "Index1"
    INDEX_2_NOVASEQ_X: str = "Index2"
    INNER_READ: str = ".//Read"
    INSTRUMENT_TYPE: str = ".InstrumentType"
    PLANNED_READS_HISEQ: str = ".//Reads"
    PLANNED_READS_NOVASEQ_X: str = "./PlannedReads"
    READ_1_HISEQ: str = ".//Read1"
    READ_2_HISEQ: str = ".//Read2"
    READ_1_NOVASEQ_6000: str = "./Read1NumberOfCycles"
    READ_2_NOVASEQ_6000: str = "./Read2NumberOfCycles"
    READ_1_NOVASEQ_X: str = "Read1"
    READ_2_NOVASEQ_X: str = "Read2"
    READ_NAME: str = "ReadName"
    REAGENT_KIT_VERSION: str = "./RfidsInfo/SbsConsumableVersion"
    SEQUENCER_ID: str = ".//ScannerID"

    # Node Values
    HISEQ_APPLICATION: str = "HiSeq Control Software"
    NOVASEQ_6000_APPLICATION: str = "NovaSeq Control Software"
    NOVASEQ_X_INSTRUMENT: str = "NovaSeqXPlus"
    UNKNOWN_REAGENT_KIT_VERSION: str = "unknown"


class SampleSheetBcl2FastqSections:
    """Class with all necessary constants for building a NovaSeqX sample sheet."""

    class Settings(Enum):
        HEADER: str = "[Settings]"
        BARCODE_MISMATCH_INDEX1: list[str] = ["BarcodeMismatchesIndex1", "0"]
        BARCODE_MISMATCH_INDEX2: list[str] = ["BarcodeMismatchesIndex2", "0"]

    class Data(Enum):
        HEADER: str = "[Data]"
        FLOW_CELL_ID: str = "FCID"
        LANE: str = "Lane"
        SAMPLE_INTERNAL_ID_BCL2FASTQ: str = "SampleID"
        SAMPLE_REFERENCE: str = "SampleRef"
        INDEX_1: str = "index"
        INDEX_2: str = "index2"
        SAMPLE_NAME: str = "SampleName"
        CONTROL: str = "Control"
        RECIPE: str = "Recipe"
        OPERATOR: str = "Operator"
        SAMPLE_PROJECT_BCL2FASTQ: str = "Project"

        COLUMN_NAMES: list[str] = [
            FLOW_CELL_ID,
            LANE,
            SAMPLE_INTERNAL_ID_BCL2FASTQ,
            SAMPLE_REFERENCE,
            INDEX_1,
            INDEX_2,
            SAMPLE_NAME,
            CONTROL,
            RECIPE,
            OPERATOR,
            SAMPLE_PROJECT_BCL2FASTQ,
        ]


class SampleSheetBCLConvertSections:
    """Class with all necessary constants for building a version 2 sample sheet."""

    class Header(Enum):
        HEADER: str = "[Header]"
        FILE_FORMAT: list[str] = ["FileFormatVersion", "2"]
        RUN_NAME: str = "RunName"
        INSTRUMENT_PLATFORM_TITLE: str = "InstrumentPlatform"
        INSTRUMENT_PLATFORM_VALUE: dict[str, str] = {
            Sequencers.NOVASEQ: "NovaSeq6000",
            Sequencers.NOVASEQX: "NovaSeqXSeries",
        }
        INDEX_ORIENTATION_FORWARD: list[str] = ["IndexOrientation", "Forward"]

    class Reads(StrEnum):
        HEADER: str = "[Reads]"
        READ_CYCLES_1: str = "Read1Cycles"
        READ_CYCLES_2: str = "Read2Cycles"
        INDEX_CYCLES_1: str = "Index1Cycles"
        INDEX_CYCLES_2: str = "Index2Cycles"

    class Settings(Enum):
        HEADER: str = "[BCLConvert_Settings]"
        SOFTWARE_VERSION: list[str] = ["SoftwareVersion", "4.1.7"]
        FASTQ_COMPRESSION_FORMAT: list[str] = ["FastqCompressionFormat", "gzip"]

    class Data(Enum):
        HEADER: str = "[BCLConvert_Data]"
        LANE: str = "Lane"
        SAMPLE_INTERNAL_ID: str = "Sample_ID"
        INDEX_1: str = "Index"
        INDEX_2: str = "Index2"
        OVERRIDE_CYCLES: str = "OverrideCycles"
        ADAPTER_READ_1: str = "AdapterRead1"
        ADAPTER_READ_2: str = "AdapterRead2"
        BARCODE_MISMATCHES_1: str = "BarcodeMismatchesIndex1"
        BARCODE_MISMATCHES_2: str = "BarcodeMismatchesIndex2"

        COLUMN_NAMES: list[str] = [
            LANE,
            SAMPLE_INTERNAL_ID,
            INDEX_1,
            INDEX_2,
            OVERRIDE_CYCLES,
            ADAPTER_READ_1,
            ADAPTER_READ_2,
            BARCODE_MISMATCHES_1,
            BARCODE_MISMATCHES_2,
        ]


OPTION_BCL_CONVERTER = click.option(
    "-b",
    "--bcl-converter",
    type=click.Choice(["bcl2fastq", "dragen"]),
    default=None,
    help="Specify bcl conversion software. Choose between bcl2fastq and dragen. "
    "If not specified, the software will be determined automatically using the sequencer type.",
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
