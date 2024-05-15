"""Mock models from the store. Used for processing them without using the store"""

import datetime

from cg.store.models import Analysis, Case, Customer


class Customer(Customer):
    """Mock a customer object"""

    def __init__(self):
        self.internal_id = "cust000"


class Case(Case):
    """Mock a case object"""

    def __init__(self):
        self.id: int = 1
        self.panels: list[str] = ["PEDHEP"]
        self.internal_id: str = "yellowhog"
        self.name: str = "analysis_family"
        self.customer: Customer = Customer()


class Analysis(Analysis):
    """Mock an store analysis object"""

    def __init__(self):
        self.id = 1
        self.completed_at = datetime.datetime.now()
        self.case: Case = Case()
