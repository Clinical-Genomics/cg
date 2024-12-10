from enum import Enum

from cg.constants import DataDelivery


class BalsamicDeliveryType(Enum):
    ANALYSIS = DataDelivery.ANALYSIS_FILES
    FASTQ_ANALYSIS = DataDelivery.FASTQ_ANALYSIS
    NO_DELIVERY = DataDelivery.NO_DELIVERY