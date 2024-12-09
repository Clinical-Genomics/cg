from enum import Enum

from cg.constants import DataDelivery


class PacbioDeliveryType(Enum):
    BAM = DataDelivery.BAM
    NO_DELIVERY = DataDelivery.NO_DELIVERY
