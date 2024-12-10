from enum import Enum


class DeliveryDestination(Enum):
    """Enum for the DeliveryDestination
    BASE: Deliver to the base folder provided in the call
    CUSTOMER: Deliver to the customer folder on hasta
    """

    BASE = "base"
    CUSTOMER = "customer"
