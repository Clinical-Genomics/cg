from enum import Enum

from cg.constants import DataDelivery


class MicroSaltDeliveryType(Enum):
    FASTQ_QC = DataDelivery.FASTQ_QC
    FASTQ_QC_ANALYSIS = DataDelivery.FASTQ_QC_ANALYSIS
    NO_DELIVERY = DataDelivery.NO_DELIVERY
