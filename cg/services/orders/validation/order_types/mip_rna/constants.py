from enum import StrEnum

from cg.constants import DataDelivery


class MIPRNADeliveryType(StrEnum):
    ANALYSIS = DataDelivery.ANALYSIS_FILES
    FASTQ = DataDelivery.FASTQ
    FASTQ_ANALYSIS = DataDelivery.FASTQ_ANALYSIS
    NO_DELIVERY = DataDelivery.NO_DELIVERY
