from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

from cg.services.validation_service.models.order_case import OrderCase


def validate_subject_id(self: OrderCase):
    error_details: list[InitErrorDetails] = []
    case_name: str = self.name
    for sample in self.samples:
        if sample.subject_id == sample.name or sample.subject_id == case_name:
            error_detail = InitErrorDetails(
                type=PydanticCustomError(
                    error_type="Subject id clash",
                    message_template="Subject ids must be different from the case name and sample name.",
                ),
                loc=("case", case_name, "sample", sample.name, "mother"),
                input=sample.subject_id,
                ctx={},
            )
            error_details.append(error_detail)
    if error_details:
        raise ValidationError.from_exception_data(
            title=self.__class__.__name__, line_errors=error_details
        )
