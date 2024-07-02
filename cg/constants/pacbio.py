"""Constants related to PacBio sequencing."""


class PacBioDirsAndFiles:
    ADAPTER_REPORT: str = "adapter.report.json"
    BASECALLING_REPORT: str = "ccs.report.json"
    CONTROL_REPORT: str = "control.report.json"
    LOADING_REPORT: str = "loading.report.json"
    RAW_DATA_REPORT: str = "raw_data.report.json"


class CCSAttributeIDs:
    NUMBER_OF_READS: str = "ccs2.number_of_ccs_reads"
    TOTAL_NUMBER_OF_BASES: str = "ccs2.total_number_of_ccs_bases"
    MEAN_READ_LENGTH: str = "ccs2.mean_ccs_readlength"
    MEDIAN_READ_LENGTH: str = "ccs2.median_ccs_readlength"
    READ_LENGTH_N50: str = "ccs2.ccs_readlength_n50"
    MEDIAN_ACCURACY: str = "ccs2.median_accuracy"
    PERCENT_Q30: str = "ccs2.percent_ccs_bases_q30"
