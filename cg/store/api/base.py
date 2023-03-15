"""All models aggregated in a base class"""
from attr import dataclass

from cg.store import models
from sqlalchemy.orm import Query


@dataclass
class BaseHandler:
    """All models in one base class"""

    User = models.User
    Bed = models.Bed
    BedVersion = models.BedVersion
    Customer = models.Customer
    Collaboration = models.Collaboration
    Sample = models.Sample
    Family = models.Family
    FamilySample = models.FamilySample
    Flowcell = models.Flowcell
    Analysis = models.Analysis
    Application = models.Application
    ApplicationVersion = models.ApplicationVersion
    Panel = models.Panel
    Pool = models.Pool
    Delivery = models.Delivery
    Invoice = models.Invoice
    Organism = models.Organism

    @staticmethod
    def _get_union_query(query: Query, query2: Query) -> Query:
        """Return a union query"""
        return query.union(query2)
