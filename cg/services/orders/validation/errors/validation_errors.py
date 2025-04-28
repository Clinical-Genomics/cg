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
        """Return True if there are no errors in any of the attributes,
        or if all the errors are actually warnings."""
        return all(
            not getattr(self, field)
            or (all(getattr(item, "field") == "warnings" for item in getattr(self, field)))
            for field in self.model_fields
        )

    def get_error_message(self) -> str:
        """Gets a string documenting all errors."""
        error_string = ""
        for error in self.order_errors:
            error_string += f"Problem with {error.field}: {error.message} \n"
        for error in self.case_errors:
            error_string += (
                f"Problem with {error.field} in case {error.case_index}: {error.message} \n"
            )
        for error in self.case_sample_errors:
            error_string += f"Problem with {error.field} in case {error.case_index} sample {error.sample_index}: {error.message} \n"
        for error in self.sample_errors:
            error_string += (
                f"Problem with {error.field} in sample {error.sample_index}: {error.message} \n"
            )
        return error_string
