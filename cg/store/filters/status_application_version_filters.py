from enum import Enum
from sqlalchemy.orm import Query
from typing import List, Callable

from cg.store.models import Application, ApplicationVersion

def filter_application_version_by_application:
    pass

def filter_application_version_by_application_id():
    pass

def filter_application_version_by_tag():
    pass

def apply_application_version_filter(
    filter_functions: List[Callable],
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    pass

class ApplicationVersionFilter(Enum):
    """Define Application Version filter functions."""
    pass
