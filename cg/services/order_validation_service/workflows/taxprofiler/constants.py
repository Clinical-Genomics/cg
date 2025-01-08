from enum import StrEnum

from cg.constants import DataDelivery


class TaxprofilerDeliveryType(StrEnum):
    ANALYSIS = DataDelivery.ANALYSIS_FILES
    FASTQ_ANALYSIS = DataDelivery.FASTQ_ANALYSIS
    NO_DELIVERY = DataDelivery.NO_DELIVERY
