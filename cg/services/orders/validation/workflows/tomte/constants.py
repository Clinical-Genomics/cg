from enum import StrEnum

from cg.constants.constants import DataDelivery


class TomteDeliveryType(StrEnum):
    ANALYSIS_FILES = DataDelivery.ANALYSIS_FILES
    FASTQ = DataDelivery.FASTQ
    FASTQ_ANALYSIS = DataDelivery.FASTQ_ANALYSIS
    NO_DELIVERY = DataDelivery.NO_DELIVERY
