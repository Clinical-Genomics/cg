from enum import StrEnum

from cg.constants import DataDelivery


class MicrosaltDeliveryType(StrEnum):
    FASTQ_QC = DataDelivery.FASTQ_QC
    FASTQ_QC_ANALYSIS = DataDelivery.FASTQ_QC_ANALYSIS
    NO_DELIVERY = DataDelivery.NO_DELIVERY
