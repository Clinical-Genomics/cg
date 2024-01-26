"""Constants related to demultiplexing."""

from enum import StrEnum
from pathlib import Path

import click
from pydantic import BaseModel

from cg.constants.sequencing import Sequencers


class BclConverter(StrEnum):
    """Define the BCL converter."""

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

    class Settings(StrEnum):
        HEADER: str = "[Settings]"

        @classmethod
        def barcode_mismatch_index_1(cls) -> list[str]:
            return ["BarcodeMismatchesIndex1", "0"]

        @classmethod
        def barcode_mismatch_index_2(cls) -> list[str]:
            return ["BarcodeMismatchesIndex2", "0"]

    class Data(StrEnum):
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

        @classmethod
        def column_names(cls) -> list[str]:
            return [
                cls.FLOW_CELL_ID,
                cls.LANE,
                cls.SAMPLE_INTERNAL_ID_BCL2FASTQ,
                cls.SAMPLE_REFERENCE,
                cls.INDEX_1,
                cls.INDEX_2,
                cls.SAMPLE_NAME,
                cls.CONTROL,
                cls.RECIPE,
                cls.OPERATOR,
                cls.SAMPLE_PROJECT_BCL2FASTQ,
            ]


class SampleSheetBCLConvertSections:
    """Class with all necessary constants for building a version 2 sample sheet."""

    class Header(StrEnum):
        HEADER: str = "[Header]"
        RUN_NAME: str = "RunName"
        INSTRUMENT_PLATFORM_TITLE: str = "InstrumentPlatform"

        @classmethod
        def file_format(cls) -> list[str]:
            return ["FileFormatVersion", "2"]

        @classmethod
        def instrument_platform_sequencer(cls) -> dict[str, str]:
            return {
                Sequencers.NOVASEQ: "NovaSeq6000",
                Sequencers.NOVASEQX: "NovaSeqXSeries",
                Sequencers.HISEQX: "HiSeqXSeries",
                Sequencers.HISEQGA: "HiSeq2500",
            }

        @classmethod
        def index_orientation_forward(cls) -> list[str]:
            return ["IndexOrientation", "Forward"]

    class Reads(StrEnum):
        HEADER: str = "[Reads]"
        READ_CYCLES_1: str = "Read1Cycles"
        READ_CYCLES_2: str = "Read2Cycles"
        INDEX_CYCLES_1: str = "Index1Cycles"
        INDEX_CYCLES_2: str = "Index2Cycles"

    class Settings(StrEnum):
        HEADER: str = "[BCLConvert_Settings]"

        @classmethod
        def software_version(cls) -> list[str]:
            return ["SoftwareVersion", "4.1.7"]

        @classmethod
        def fastq_compression_format(cls) -> list[str]:
            return ["FastqCompressionFormat", "gzip"]

    class Data(StrEnum):
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

        @classmethod
        def column_names(cls) -> list[str]:
            return [
                cls.LANE,
                cls.SAMPLE_INTERNAL_ID,
                cls.INDEX_1,
                cls.INDEX_2,
                cls.OVERRIDE_CYCLES,
                cls.ADAPTER_READ_1,
                cls.ADAPTER_READ_2,
                cls.BARCODE_MISMATCHES_1,
                cls.BARCODE_MISMATCHES_2,
            ]


class IndexOverrideCycles(StrEnum):
    """Class with the possible values that index cycles can take."""

    FULL_10_INDEX: str = "I10;"
    FULL_8_INDEX: str = "I8;"
    IGNORED_10_INDEX: str = "N10;"
    IGNORED_8_INDEX: str = "N8;"
    INDEX_8_IGNORED_2: str = "I8N2;"
    INDEX_8_IGNORED_2_REVERSED: str = "N2I8;"


OPTION_BCL_CONVERTER = click.option(
    "-b",
    "--bcl-converter",
    type=click.Choice([BclConverter.BCL2FASTQ, BclConverter.BCLCONVERT]),
    default=None,
    help="Specify bcl conversion software. Choose between bcl2fastq and dragen. "
    "If not specified, the software will be determined automatically using the sequencer type.",
)


DEMUX_STATS_PATH: dict[str, dict[str, Path | None]] = {
    BclConverter.BCL2FASTQ: {
        "demultiplexing_stats": Path("Stats", "DemultiplexingStats.xml"),
        "conversion_stats": Path("Stats", "ConversionStats.xml"),
        "runinfo": None,
    },
    BclConverter.BCLCONVERT: {
        "demultiplexing_stats": Path("Reports", "Demultiplex_Stats.csv"),
        "conversion_stats": Path("Reports", "Demultiplex_Stats.csv"),
        "adapter_metrics_stats": Path("Reports", "Adapter_Metrics.csv"),
        "runinfo": Path("Reports", "RunInfo.xml"),
        "quality_metrics": Path("Reports", "Quality_Metrics.csv"),
    },
}

BCL2FASTQ_METRICS_DIRECTORY_NAME: str = "Stats"
BCL2FASTQ_METRICS_FILE_NAME: str = "Stats.json"
CUSTOM_INDEX_TAIL = "NNNNNNNNN"
DRAGEN_PASSED_FILTER_PCT: float = 100.00000
FASTQ_FILE_SUFFIXES: list[str] = [".fastq", ".gz"]
INDEX_CHECK: str = "indexcheck"
UNDETERMINED: str = "Undetermined"

NEW_NOVASEQ_CONTROL_SOFTWARE_VERSION: str = "1.7.0"
NEW_NOVASEQ_REAGENT_KIT_VERSION: str = "1.5"


class IndexSettings(BaseModel):
    """
    Holds the settings defining how the sample indexes should be handled in the sample sheet.
    These vary between machines and versions.

        Attributes:
            should_i5_be_reverse_complemented (bool): Whether the i5 index should be reverse complemented.
            are_i5_override_cycles_reverse_complemented (bool): Whether the override cycles for i5 should be written in as NXIX.

    """

    should_i5_be_reverse_complemented: bool
    are_i5_override_cycles_reverse_complemented: bool


# The logic for the settings below are acquired empirically, any changes should be well motivated
# and rigorously tested.

NOVASEQ_X_INDEX_SETTINGS = IndexSettings(
    should_i5_be_reverse_complemented=False, are_i5_override_cycles_reverse_complemented=True
)
NOVASEQ_6000_POST_1_5_KITS_INDEX_SETTINGS = IndexSettings(
    should_i5_be_reverse_complemented=True, are_i5_override_cycles_reverse_complemented=False
)
NO_REVERSE_COMPLEMENTS_INDEX_SETTINGS = IndexSettings(
    should_i5_be_reverse_complemented=False,
    are_i5_override_cycles_reverse_complemented=False,
)
