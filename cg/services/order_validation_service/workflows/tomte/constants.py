from enum import Enum

from cg.constants.constants import DataDelivery


class TomteDeliveryType(Enum):
    DataDelivery.ANALYSIS_FILES,
    DataDelivery.FASTQ,
    DataDelivery.FASTQ_ANALYSIS,
    DataDelivery.NO_DELIVERY,
