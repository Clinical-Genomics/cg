from enum import Enum


class DeliveryDestination(Enum):
    """Enum for the DeliveryDestination
    BASE: Deliver to the base folder provided in the call
    CUSTOMER: Deliver to the customer folder on hasta
    FOHM: Deliver to the FOHM folder on hasta
    """

    BASE = "base"
    CUSTOMER = "customer"
    FOHM = "fohm"


class DeliveryStructure(Enum):
    """Enum for the DeliveryStructure
    FLAT: Deliver the files in a flat structure, i.e. all files in the same folder
    NESTED: Deliver the files in a nested structure, i.e. files in folders for each sample/case
    """

    FLAT: str = "flat"
    NESTED: str = "nested"
