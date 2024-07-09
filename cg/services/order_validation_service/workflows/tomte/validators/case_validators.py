from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError
from cg.constants import DataDelivery
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample

TOMTE_DELIVERY_TYPES = [
    DataDelivery.ANALYSIS_FILES,
    DataDelivery.FASTQ,
    DataDelivery.FASTQ_ANALYSIS,
    DataDelivery.NO_DELIVERY,
]


def validate_delivery_type(delivery_type: DataDelivery):
    if delivery_type not in TOMTE_DELIVERY_TYPES:
        raise ValueError("Delivery type not allowed.")

def validate_mothers(samples: list[TomteSample]):
    sample_names = [sample.name for sample in samples]
    error_details: list[InitErrorDetails] = []
    for sample in samples:
        if sample.mother and sample.mother not in sample_names:
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


def validate_fathers(samples: list[TomteSample]):
    sample_names = [sample.name for sample in samples]
    error_details: list[InitErrorDetails] = []
    for sample in samples:
        if sample.father and sample.father not in sample_names:
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


def validate_subject_id(case: TomteCase):
    error_details: list[InitErrorDetails] = []
    case_name: str = case.name
    for sample in case.samples:
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
            title=case.__class__.__name__, line_errors=error_details
        )
