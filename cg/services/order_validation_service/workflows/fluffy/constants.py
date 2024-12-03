from enum import Enum

from cg.constants import DataDelivery


class FluffyDeliveryType(Enum):
    STATINA = DataDelivery.STATINA
    NO_DELIVERY = DataDelivery.NO_DELIVERY
