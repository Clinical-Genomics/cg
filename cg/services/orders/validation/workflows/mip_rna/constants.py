from enum import StrEnum

from cg.constants import DataDelivery


class MIPRNADeliveryType(StrEnum):
    ANALYSIS = DataDelivery.ANALYSIS_FILES
    ANALYSIS_SCOUT = DataDelivery.ANALYSIS_SCOUT
    SCOUT = DataDelivery.SCOUT
    FASTQ = DataDelivery.FASTQ
    FASTQ_ANALYSIS = DataDelivery.FASTQ_ANALYSIS
    FASTQ_SCOUT = DataDelivery.FASTQ_SCOUT
    FASTQ_ANALYSIS_SCOUT = DataDelivery.FASTQ_ANALYSIS_SCOUT
    NO_DELIVERY = DataDelivery.NO_DELIVERY
