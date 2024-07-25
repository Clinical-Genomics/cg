"""Constants related to PacBio sequencing."""

from cg.constants import FileExtensions
from cg.constants.housekeeper_tags import AlignmentFileTag


class PacBioDirsAndFiles:
    BASECALLING_REPORT: str = "ccs.report.json"
    CCS_REPORT_SUFFIX: str = "ccs_report.json"
    CONTROL_REPORT: str = "control.report.json"
    LOADING_REPORT: str = "loading.report.json"
    HIFI_READS: str = "hifi_reads"
    RAW_DATA_REPORT: str = "raw_data.report.json"
    SMRTLINK_DATASETS_REPORT: str = "smrtlink-datasets.json"
    STATISTICS_DIR: str = "statistics"
    UNZIPPED_REPORTS_DIR: str = "unzipped_reports"


class CCSAttributeIDs:
    NUMBER_OF_READS: str = "ccs2.number_of_ccs_reads"
    TOTAL_NUMBER_OF_BASES: str = "ccs2.total_number_of_ccs_bases"
    MEAN_READ_LENGTH: str = "ccs2.mean_ccs_readlength"
    MEDIAN_READ_LENGTH: str = "ccs2.median_ccs_readlength"
    READ_LENGTH_N50: str = "ccs2.ccs_readlength_n50"
    MEDIAN_ACCURACY: str = "ccs2.median_accuracy"
    PERCENT_Q30: str = "ccs2.percent_ccs_bases_q30"


class ControlAttributeIDs:
    NUMBER_OF_READS: str = "control.reads_n"
    MEAN_READ_LENGTH: str = "control.readlength_mean"
    PERCENT_MEAN_READ_CONCORDANCE: str = "control.concordance_mean"
    PERCENT_MODE_READ_CONCORDANCE: str = "control.concordance_mode"


class LoadingAttributesIDs:
    PRODUCTIVE_ZMWS: str = "loading_xml_report.productive_zmws"
    P_0: str = "loading_xml_report.productivity_0_n"
    P_1: str = "loading_xml_report.productivity_1_n"
    P_2: str = "loading_xml_report.productivity_2_n"


class PolymeraseDataAttributeIDs:
    MEAN_READ_LENGTH: str = "raw_data_report.read_length"
    READ_LENGTH_N50: str = "raw_data_report.read_n50"
    MEAN_LONGEST_SUBREAD_LENGTH: str = "raw_data_report.insert_length"
    LONGEST_SUBREAD_LENGTH_N50: str = "raw_data_report.insert_n50"


class SmrtLinkDatabasesIDs:
    BIO_SAMPLE_NAME: str = "bioSampleName"
    CELL_ID: str = "cellId"
    CELL_INDEX: str = "cellIndex"
    MOVIE_NAME: str = "metadataContextId"
    PATH: str = "path"
    WELL_NAME: str = "wellName"
    WELL_SAMPLE_NAME: str = "wellSampleName"


class PacBioHousekeeperTags:
    CCS_REPORT: str = "ccs-report"
    CONTROL_REPORT: str = "control-report"
    LOADING_REPORT: str = "loading-report"
    RAWDATA_REPORT: str = "raw-data-report"
    DATASETS_REPORT: str = "datasets-report"


class PacBioBundleTypes:
    SAMPLE: str = "sample"
    SMRT_CELL: str = "smrt_cell"


file_pattern_to_tag: dict[str, list[str]] = {
    f"*{PacBioDirsAndFiles.CONTROL_REPORT}*": [PacBioHousekeeperTags.CONTROL_REPORT],
    f"*{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}*": [PacBioHousekeeperTags.CCS_REPORT],
    f"*{PacBioDirsAndFiles.LOADING_REPORT}*": [PacBioHousekeeperTags.LOADING_REPORT],
    f"*{PacBioDirsAndFiles.RAW_DATA_REPORT}*": [PacBioHousekeeperTags.RAWDATA_REPORT],
    f"*{PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT}*": [PacBioHousekeeperTags.DATASETS_REPORT],
    f"*{PacBioDirsAndFiles.HIFI_READS}*{FileExtensions.BAM}*": [AlignmentFileTag.BAM],
}

file_pattern_to_bundle_type: dict[str, str] = {
    f"*{PacBioDirsAndFiles.CONTROL_REPORT}*": PacBioBundleTypes.SMRT_CELL,
    f"*{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}*": PacBioBundleTypes.SMRT_CELL,
    f"*{PacBioDirsAndFiles.LOADING_REPORT}*": PacBioBundleTypes.SMRT_CELL,
    f"*{PacBioDirsAndFiles.RAW_DATA_REPORT}*": PacBioBundleTypes.SMRT_CELL,
    f"*{PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT}*": PacBioBundleTypes.SMRT_CELL,
    f"*{PacBioDirsAndFiles.HIFI_READS}*{FileExtensions.BAM}*": PacBioBundleTypes.SAMPLE,
}
