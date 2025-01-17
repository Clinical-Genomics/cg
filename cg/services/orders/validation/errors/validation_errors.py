from pydantic import BaseModel

from cg.services.orders.validation.errors.case_errors import CaseError
from cg.services.orders.validation.errors.case_sample_errors import CaseSampleError
from cg.services.orders.validation.errors.order_errors import OrderError
from cg.services.orders.validation.errors.sample_errors import SampleError


class ValidationErrors(BaseModel):
    order_errors: list[OrderError] = []
    case_errors: list[CaseError] = []
    sample_errors: list[SampleError] = []
    case_sample_errors: list[CaseSampleError] = []

    @property
    def is_empty(self) -> bool:
        """Return True if there are no errors in any of the attributes."""
        return all(not getattr(self, field) for field in self.model_fields)
