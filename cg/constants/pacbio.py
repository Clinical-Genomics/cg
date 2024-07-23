"""Constants related to PacBio sequencing."""


class PacBioDirsAndFiles:
    ADAPTER_REPORT: str = "adapter.report.json"
    BASECALLING_REPORT: str = "ccs.report.json"
    CONTROL_REPORT: str = "control.report.json"
    LOADING_REPORT: str = "loading.report.json"
    RAW_DATA_REPORT: str = "raw_data.report.json"
    SMRTLINK_DATASETS_REPORT: str = "smrtlink-datasets.json"
    CCS_REPORT_SUFFIX: str = "ccs_report.json"


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
