from enum import StrEnum

from cg.constants.constants import DataDelivery


class TomteDeliveryType(StrEnum):
    ANALYSIS_FILES = DataDelivery.ANALYSIS_FILES
    ANALYSIS_SCOUT = DataDelivery.ANALYSIS_SCOUT
    FASTQ = DataDelivery.FASTQ
    FASTQ_ANALYSIS = DataDelivery.FASTQ_ANALYSIS
    FASTQ_ANALYSIS_SCOUT = DataDelivery.FASTQ_ANALYSIS_SCOUT
    FASTQ_SCOUT = DataDelivery.FASTQ_SCOUT
    NO_DELIVERY = DataDelivery.NO_DELIVERY
    SCOUT = DataDelivery.SCOUT
