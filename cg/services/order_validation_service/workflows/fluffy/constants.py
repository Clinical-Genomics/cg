from enum import Enum

from cg.constants import DataDelivery


class fluffyDeliveryType(Enum):
    SCOUT = DataDelivery.SCOUT
    NO_DELIVERY = DataDelivery.NO_DELIVERY
