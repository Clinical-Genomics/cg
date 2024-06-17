"""Constants related to demultiplexing."""

from enum import Enum, StrEnum

from pydantic import BaseModel

from cg.constants.sequencing import Sequencers


class DemultiplexingDirsAndFiles(StrEnum):
    """Demultiplexing related directories and files."""

    COPY_COMPLETE: str = "CopyComplete.txt"
    DELIVERY: str = "delivery.txt"
    DEMUX_STARTED: str = "demuxstarted.txt"
    DEMUX_COMPLETE: str = "demuxcomplete.txt"
    RTACOMPLETE: str = "RTAComplete.txt"
    RUN_PARAMETERS_PASCAL_CASE: str = "RunParameters.xml"
    RUN_PARAMETERS_CAMEL_CASE: str = "runParameters.xml"
    SAMPLE_SHEET_FILE_NAME: str = "SampleSheet.csv"
    UNALIGNED_DIR_NAME: str = "Unaligned"
    QUEUED_FOR_POST_PROCESSING: str = "post_processing_queued.txt"
    ANALYSIS_COMPLETED: str = "Secondary_Analysis_Complete.txt"
    ANALYSIS: str = "Analysis"
    DATA: str = "Data"
    BCL_CONVERT: str = "BCLConvert"
    SEQUENCING_RUNS_DIRECTORY_NAME: str = "sequencing-runs"
    DEMULTIPLEXED_RUNS_DIRECTORY_NAME: str = "demultiplexed-runs"
    ILLUMINA_FILE_MANIFEST: str = "Manifest.tsv"
    CG_FILE_MANIFEST: str = "file_manifest.tsv"
    INTER_OP: str = "InterOp"
    RUN_COMPLETION_STATUS: str = "RunCompletionStatus.xml"
    DEMUX_VERSION_FILE: str = "dragen-replay.json"


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
    FLOW_CELL_MODE: str = ".//FlowCellMode"
    MODE: str = ".//Mode"

    # Node Values
    HISEQ_APPLICATION: str = "HiSeq Control Software"
    NOVASEQ_6000_APPLICATION: str = "NovaSeq Control Software"
    NOVASEQ_X_INSTRUMENT: str = "NovaSeqXPlus"
    UNKNOWN_REAGENT_KIT_VERSION: str = "unknown"


class SampleSheetBcl2FastqSections:
    """Class with all necessary constants for building a NovaSeqX sample sheet."""

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


class SampleSheetBCLConvertSections:
    """Class with all necessary constants for building a version 2 sample sheet."""

    class Header(StrEnum):
        HEADER: str = "[Header]"
        RUN_NAME: str = "RunName"
        INSTRUMENT_PLATFORM_TITLE: str = "InstrumentPlatform"
        INDEX_SETTINGS: str = "IndexSettings"

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


CUSTOM_INDEX_TAIL = "NNNNNNNNN"
FASTQ_FILE_SUFFIXES: list[str] = [".fastq", ".gz"]
UNDETERMINED: str = "Undetermined"

NEW_NOVASEQ_CONTROL_SOFTWARE_VERSION: str = "1.7.0"
NEW_NOVASEQ_REAGENT_KIT_VERSION: str = "1.5"

FORWARD_INDEX_CYCLE_PATTERN: str = r"I(\d+)N(\d+)"
REVERSE_INDEX_CYCLE_PATTERN: str = r"N(\d+)I(\d+)"


class IndexSettings(BaseModel):
    """
    Holds the settings defining how the sample indexes should be handled in the sample sheet.
    These vary between machines and versions.

        Attributes:
            should_i5_be_reverse_complemented (bool): Whether the i5 index should be reverse complemented.
            are_i5_override_cycles_reverse_complemented (bool): Whether the override cycles for i5 should be written in as NXIX.

    """

    name: str
    should_i5_be_reverse_complemented: bool
    are_i5_override_cycles_reverse_complemented: bool


# The logic for the settings below are acquired empirically, any changes should be well motivated
# and rigorously tested.

NOVASEQ_X_INDEX_SETTINGS = IndexSettings(
    name="NovaSeqX",
    should_i5_be_reverse_complemented=False,
    are_i5_override_cycles_reverse_complemented=True,
)
NOVASEQ_6000_POST_1_5_KITS_INDEX_SETTINGS = IndexSettings(
    name="NovaSeq6000Post1.5Kits",
    should_i5_be_reverse_complemented=True,
    are_i5_override_cycles_reverse_complemented=False,
)
NO_REVERSE_COMPLEMENTS_INDEX_SETTINGS = IndexSettings(
    name="NoReverseComplements",
    should_i5_be_reverse_complemented=False,
    are_i5_override_cycles_reverse_complemented=False,
)

NAME_TO_INDEX_SETTINGS: dict[str, IndexSettings] = {
    "NovaSeqX": NOVASEQ_X_INDEX_SETTINGS,
    "NovaSeq6000Post1.5Kits": NOVASEQ_6000_POST_1_5_KITS_INDEX_SETTINGS,
    "NoReverseComplements": NO_REVERSE_COMPLEMENTS_INDEX_SETTINGS,
}


class RunCompletionStatusNodes(StrEnum):
    RUN_START: str = ".//RunStartTime"
    RUN_END: str = ".//RunEndTime"
