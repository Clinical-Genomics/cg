"""Constants related to PacBio sequencing."""

from cg.constants import FileExtensions


class PacBioDirsAndFiles:
    BARCODES_REPORT: str = "barcodes.report.json"
    CCS_REPORT_SUFFIX: str = "ccs_report.json"
    CONTROL_REPORT: str = "control.report.json"
    LOADING_REPORT: str = "loading.report.json"
    HIFI_READS: str = "hifi_reads"
    RAW_DATA_REPORT: str = "raw_data.report.json"
    SMRTLINK_DATASETS_REPORT: str = "smrtlink-datasets.json"
    STATISTICS_DIR: str = "statistics"
    UNZIPPED_REPORTS_DIR: str = "unzipped_reports"
    METADATA_DIR: str = "metadata"
    RUN_IS_VALID: str = "is_valid"


class MetricsFileFields:
    ATTRIBUTES: str = "attributes"
    COLUMNS: str = "columns"
    ID: str = "id"
    TABLES: str = "tables"
    VALUE: str = "value"
    VALUES: str = "values"


class CCSAttributeAliases:
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


class ControlAttributeAliases:
    NUMBER_OF_READS: str = "control.reads_n"
    MEAN_READ_LENGTH: str = "control.readlength_mean"
    PERCENT_MEAN_READ_CONCORDANCE: str = "control.concordance_mean"
    PERCENT_MODE_READ_CONCORDANCE: str = "control.concordance_mode"


class LoadingAttributesAliases:
    PRODUCTIVE_ZMWS: str = "loading_xml_report.productive_zmws"
    P_0: str = "loading_xml_report.productivity_0_n"
    P_1: str = "loading_xml_report.productivity_1_n"
    P_2: str = "loading_xml_report.productivity_2_n"


class PolymeraseDataAttributeAliases:
    MEAN_READ_LENGTH: str = "raw_data_report.read_length"
    READ_LENGTH_N50: str = "raw_data_report.read_n50"
    MEAN_LONGEST_SUBREAD_LENGTH: str = "raw_data_report.insert_length"
    LONGEST_SUBREAD_LENGTH_N50: str = "raw_data_report.insert_n50"


class SmrtLinkDatabasesAliases:
    BIO_SAMPLE_NAME: str = "bioSampleName"
    CELL_ID: str = "cellId"
    CELL_INDEX: str = "cellIndex"
    MOVIE_NAME: str = "metadataContextId"
    PATH: str = "path"
    RUN_COMPLETED_AT = "createdAt"
    WELL_NAME: str = "wellName"
    WELL_SAMPLE_NAME: str = "wellSampleName"


class BarcodeMetricsAliases:
    BARCODED_HIFI_READS: str = "barcode.n_barcoded_reads"
    BARCODED_HIFI_READS_PERCENTAGE: str = "barcode.percent_barcoded_reads"
    BARCODED_HIFI_YIELD: str = "barcode.barcoded_bases"
    BARCODED_HIFI_YIELD_PERCENTAGE: str = "barcode.percent_barcoded_bases"
    BARCODED_MEAN_READ_LENGTH: str = "barcode.n_barcoded_readlength_mean"
    UNBARCODED_HIFI_READS: str = "barcode.n_unbarcoded_reads"
    UNBARCODED_HIFI_YIELD: str = "barcode.unbarcoded_bases"
    UNBARCODED_HIFI_MEAN_READ_LENGTH: str = "barcode.mean_unbarcoded_read_length"


class SampleMetricsAliases:
    BARCODE_NAME: str = "barcode.barcode_table.barcode"
    HIFI_MEAN_READ_LENGTH: str = "barcode.barcode_table.mean_read_length"
    HIFI_READ_QUALITY: str = "barcode.barcode_table.median_read_quality"
    HIFI_READS: str = "barcode.barcode_table.number_of_reads"
    HIFI_YIELD: str = "barcode.barcode_table.number_of_bases"
    POLYMERASE_READ_LENGTH: str = "barcode.barcode_table.mean_polymerase_read_length"
    SAMPLE_INTERNAL_ID: str = "barcode.barcode_table.biosample"


class PacBioHousekeeperTags:
    BARCODES_REPORT: str = "barcodes-report"
    CCS_REPORT: str = "ccs-report"
    CONTROL_REPORT: str = "control-report"
    LOADING_REPORT: str = "loading-report"
    RAWDATA_REPORT: str = "raw-data-report"
    DATASETS_REPORT: str = "datasets-report"


class PacBioBundleTypes:
    SAMPLE: str = "sample"
    SMRT_CELL: str = "smrt_cell"


file_pattern_to_bundle_type: dict[str, str] = {
    PacBioDirsAndFiles.BARCODES_REPORT: PacBioBundleTypes.SMRT_CELL,
    PacBioDirsAndFiles.CONTROL_REPORT: PacBioBundleTypes.SMRT_CELL,
    f".*{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}$": PacBioBundleTypes.SMRT_CELL,
    PacBioDirsAndFiles.LOADING_REPORT: PacBioBundleTypes.SMRT_CELL,
    PacBioDirsAndFiles.RAW_DATA_REPORT: PacBioBundleTypes.SMRT_CELL,
    PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT: PacBioBundleTypes.SMRT_CELL,
    f"{PacBioDirsAndFiles.HIFI_READS}.*{FileExtensions.BAM}$": PacBioBundleTypes.SAMPLE,
}

ZIPPED_REPORTS_PATTERN: str = "*reports.zip"
MANIFEST_FILE_PATTERN: str = "*.transferdone"
