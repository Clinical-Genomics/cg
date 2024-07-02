from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

from cg.services.validation_service.models.order_sample import OrderSample


def validate_mothers(samples: list[OrderSample]):
    sample_names = [sample.name for sample in samples]
    error_details: list[InitErrorDetails] = []
    for sample in samples:
        if sample.mother not in sample_names:
            error_detail = InitErrorDetails(
                type=PydanticCustomError(
                    error_type="Mother missing",
                    message_template="The provided mother needs to be in the case.",
                ),
                loc=("sample", sample.name, "mother"),
                input=sample.mother,
                ctx={},
            )
            error_details.append(error_detail)
    if error_details:
        raise ValidationError.from_exception_data(title="Mothers", line_errors=error_details)


def validate_fathers(samples: list[OrderSample]):
    sample_names = [sample.name for sample in samples]
    error_details: list[InitErrorDetails] = []
    for sample in samples:
        if sample.father not in sample_names:
            error_detail = InitErrorDetails(
                type=PydanticCustomError(
                    error_type="Father missing",
                    message_template="The provided father needs to be in the case.",
                ),
                loc=("sample", sample.name, "father"),
                input=sample.father,
                ctx={},
            )
            error_details.append(error_detail)
    if error_details:
        raise ValidationError.from_exception_data(title="Fathers", line_errors=error_details)
