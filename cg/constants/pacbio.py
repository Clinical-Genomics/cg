"""Constants related to PacBio sequencing."""

from cg.constants import FileExtensions


class PacBioDirsAndFiles:
    CCS_REPORT_SUFFIX: str = "ccs_report.json"
    CONTROL_REPORT: str = "control.report.json"
    LOADING_REPORT: str = "loading.report.json"
    HIFI_READS: str = "hifi_reads"
    RAW_DATA_REPORT: str = "raw_data.report.json"
    SMRTLINK_DATASETS_REPORT: str = "smrtlink-datasets.json"
    STATISTICS_DIR: str = "statistics"
    UNZIPPED_REPORTS_DIR: str = "unzipped_reports"


class CCSAttributeIDs:
    HIFI_READS: str = "ccs_processing.number_of_ccs_reads_q20"
    HIFI_YIELD: str = "ccs_processing.total_number_of_ccs_bases_q20"
    HIFI_MEAN_READ_LENGTH: str = "ccs_processing.mean_ccs_readlength_q20"
    HIFI_MEDIAN_READ_LENGTH: str = "ccs_processing.median_ccs_readlength_q20"
    HIFI_READ_LENGTH_N50: str = "ccs_processing.ccs_readlength_n50_q20"
    HIFI_MEDIAN_READ_QUALITY: str = "ccs_processing.median_qv_q20"
    PERCENT_Q30: str = "ccs_processing.base_percentage_q30"
    FAILED_READS: str = "ccs_processing.number_of_ccs_reads_lq"
    FAILED_YIELD: str = "ccs_processing.total_number_of_ccs_bases_lq"
    FAILED_MEAN_READ_LENGTH: str = "ccs_processing.mean_ccs_readlength_lq"


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
    RUN_COMPLETED_AT = "createdAt"
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


file_pattern_to_bundle_type: dict[str, str] = {
    PacBioDirsAndFiles.CONTROL_REPORT: PacBioBundleTypes.SMRT_CELL,
    f".*{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}$": PacBioBundleTypes.SMRT_CELL,
    PacBioDirsAndFiles.LOADING_REPORT: PacBioBundleTypes.SMRT_CELL,
    PacBioDirsAndFiles.RAW_DATA_REPORT: PacBioBundleTypes.SMRT_CELL,
    PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT: PacBioBundleTypes.SMRT_CELL,
    f"{PacBioDirsAndFiles.HIFI_READS}{FileExtensions.BAM}$": PacBioBundleTypes.SAMPLE,
}
