"""All models aggregated in a base class"""
from attr import dataclass

from cg.store.models import (
    User,
    BedVersion,
    Bed,
    Customer,
    Collaboration,
    Sample,
    Family,
    FamilySample,
    Flowcell,
    Analysis,
    Application,
    ApplicationVersion,
    Panel,
    Pool,
    Delivery,
    Invoice,
    Organism,
)


@dataclass
class BaseHandler:
    """All models in one base class"""

    User = User
    Bed = Bed
    BedVersion = BedVersion
    Customer = Customer
    Collaboration = Collaboration
    Sample = Sample
    Family = Family
    FamilySample = FamilySample
    Flowcell = Flowcell
    Analysis = Analysis
    Application = Application
    ApplicationVersion = ApplicationVersion
    Panel = Panel
    Pool = Pool
    Delivery = Delivery
    Invoice = Invoice
    Organism = Organism
