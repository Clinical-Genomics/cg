from enum import Enum

from cg.constants import DataDelivery


class FluffyDeliveryType(Enum):
    SCOUT = DataDelivery.STATINA
    NO_DELIVERY = DataDelivery.NO_DELIVERY
