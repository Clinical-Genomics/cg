from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

from cg.services.validation_service.models.order_sample import OrderSample


def validate_required_buffer(self: OrderSample) -> OrderSample:
    if (
        self.application.startswith("PAN")
        or self.application.startswith("EX")
        and not self.elution_buffer
    ):
        error_detail = InitErrorDetails(
            type=PydanticCustomError(
                error_type="Missing buffer",
                message_template="Buffer is required when running PAN or EX applications.",
            ),
            loc=("sample", self.name, "elution_buffer"),
            input=self.elution_buffer,
            ctx={},
        )
        raise ValidationError.from_exception_data(title="FFPE source", line_errors=[error_detail])
    return self


def validate_FFPE_source(self: OrderSample) -> OrderSample:
    if "FFPE" in str(self.source) and self.application.startswith("WG"):
        error_detail = InitErrorDetails(
            type=PydanticCustomError(
                error_type="WGS with FFPE source",
                message_template="FFPE sources are not allowed for whole genome sequencing.",
            ),
            loc=("sample", self.name, "source"),
            input=self.source,
            ctx={},
        )
        raise ValidationError.from_exception_data(title="FFPE source", line_errors=[error_detail])

    return self
