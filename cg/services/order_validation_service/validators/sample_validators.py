from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.models.order_sample import OrderSample


def validate_required_buffer(sample: OrderSample) -> OrderSample:
    if (
        sample.application.startswith("PAN")
        or sample.application.startswith("EX")
        and not sample.elution_buffer
    ):
        error_detail = InitErrorDetails(
            type=PydanticCustomError(
                error_type="Missing buffer",
                message_template="Buffer is required when running PAN or EX applications.",
            ),
            loc=("sample", sample.name, "elution_buffer"),
            input=sample.elution_buffer,
            ctx={},
        )
        raise ValidationError.from_exception_data(title="FFPE source", line_errors=[error_detail])
    return sample


def validate_ffpe_source(self: OrderSample) -> OrderSample:
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


def validate_required_container_name(sample: OrderSample):
    if sample.container == ContainerEnum.plate and not sample.container_name:
        error_details = InitErrorDetails(
            type="missing", loc=("container_name",), input=sample.container_name, ctx={}
        )
        raise ValidationError.from_exception_data(
            title=sample.__class__.__name__, line_errors=[error_details]
        )
    return sample


def validate_required_well_position(sample: OrderSample):
    if sample.container == ContainerEnum.plate and not sample.well_position:
        error_details = InitErrorDetails(
            type="missing", loc=("well_position",), input=sample.well_position, ctx={}
        )
        raise ValidationError.from_exception_data(
            title=sample.__class__.__name__, line_errors=[error_details]
        )


def validate_required_volume(sample: OrderSample):
    if sample.container != ContainerEnum.no_container and not sample.volume:
        error_details = InitErrorDetails(
            type="missing", loc=("volume",), input=sample.well_position, ctx={}
        )
        raise ValidationError.from_exception_data(
            title=sample.__class__.__name__, line_errors=[error_details]
        )
