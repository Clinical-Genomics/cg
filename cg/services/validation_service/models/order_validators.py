from pydantic import ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError

from cg.services.validation_service.models.order_case import OrderCase


def validate_well_positions(cases: list[OrderCase]):
    error_details = []
    samples_per_well = _build_well_position_sample_map(cases)
    for well in samples_per_well.keys():
        if len(samples_per_well[well]) > 1:
            error_details += _build_errors_for_well(samples=samples_per_well[well], well=well)
    if error_details:
        raise ValidationError.from_exception_data(title="Well positions", line_errors=error_details)


def _build_well_position_sample_map(cases: list[OrderCase]) -> dict:
    samples_per_well: dict = {}
    for case in cases:
        for sample in case.samples:
            if samples_per_well.get(f"{sample.container_name} {sample.well_position}"):
                samples_per_well[sample.well_position] += [(case.name, sample.name)]
            else:
                samples_per_well[f"{sample.container_name} {sample.well_position}"] = [
                    (case.name, sample.name)
                ]
    return samples_per_well


def _build_errors_for_well(samples: list[tuple], well: str):
    error_details = []
    for case_and_sample in samples:
        error_detail = InitErrorDetails(
            type=PydanticCustomError(
                error_type="Reused well",
                message_template="There can only be one sample per well.",
            ),
            loc=("case", case_and_sample[0], "sample", case_and_sample[1], "well_position"),
            input=well,
            ctx={},
        )
        error_details.append(error_detail)
    return error_details
