"""Mock models from the store. Used for processing them without using the store"""
import datetime
from typing import List

from cg.store.models import Analysis, Customer, Family


class Customer(Customer):
    """Mock a customer object"""

    def __init__(self):
        self.internal_id = "cust000"


class Family(Family):
    """Mock a case object"""

    def __init__(self):
        self.id: int = 1
        self.panels: List[str] = ["PEDHEP"]
        self.internal_id: str = "yellowhog"
        self.name: str = "analysis_family"
        self.customer: Customer = Customer()


class Analysis(Analysis):
    """Mock an store analysis object"""

    def __init__(self):
        self.id = 1
        self.completed_at = datetime.datetime.now()
        self.family: Family = Family()
