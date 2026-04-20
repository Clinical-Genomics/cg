from enum import StrEnum

from cg.constants import DataDelivery


class MIPRNADeliveryType(StrEnum):
    ANALYSIS = DataDelivery.ANALYSIS_FILES
    ANALYSIS_SCOUT = DataDelivery.ANALYSIS_SCOUT
    FASTQ = DataDelivery.FASTQ
    FASTQ_ANALYSIS = DataDelivery.FASTQ_ANALYSIS
    NO_DELIVERY = DataDelivery.NO_DELIVERY
