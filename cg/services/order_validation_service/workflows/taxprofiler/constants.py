from enum import Enum

from cg.constants import DataDelivery


class TaxprofilerDeliveryType(Enum):
    FASTQ = DataDelivery.FASTQ
    NO_DELIVERY = DataDelivery.NO_DELIVERY
