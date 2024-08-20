from pydantic import BaseModel

from cg.services.order_validation_service.constants import (
    MAXIMUM_VOLUME,
    MINIMUM_VOLUME,
)
from cg.services.order_validation_service.errors.case_errors import CaseError
from cg.services.order_validation_service.errors.sample_errors import SampleError


class CaseSampleError(CaseError, SampleError):
    pass


class OccupiedWellError(CaseSampleError):
    field: str = "well_position"
    message: str = "Well is already occupied"


class ApplicationArchivedError(CaseSampleError):
    field: str = "application"
    message: str = "Chosen application is archived"


class ApplicationNotValidError(CaseSampleError):
    field: str = "application"
    message: str = "Chosen application does not exist"


class ApplicationNotCompatibleError(CaseSampleError):
    field: str = "application"
    message: str = "Application is not allowed for the chosen workflow"


class RepeatedSampleNameError(CaseSampleError):
    field: str = "name"
    message: str = "Sample name already used"


class InvalidFatherSexError(CaseSampleError):
    field: str = "father"
    message: str = "Father must be male"


class FatherNotInCaseError(CaseSampleError):
    field: str = "father"
    message: str = "Father must be in the same case"


class InvalidMotherSexError(CaseSampleError):
    field: str = "mother"
    message: str = "Mother must be female"


class PedigreeError(CaseSampleError):
    message: str = "Invalid pedigree relationship"


class DescendantAsMotherError(PedigreeError):
    field: str = "mother"
    message: str = "Descendant sample cannot be mother"


class DescendantAsFatherError(PedigreeError):
    field: str = "father"
    message: str = "Descendant sample cannot be father"


class SampleIsOwnMotherError(PedigreeError):
    field: str = "mother"
    message: str = "Sample cannot be its own mother"


class SampleIsOwnFatherError(PedigreeError):
    field: str = "father"
    message: str = "Sample cannot be its own father"


class MotherNotInCaseError(CaseSampleError):
    field: str = "mother"
    message: str = "Mother must be in the same case"


class StatusMissingError(CaseSampleError):
    field: str = "status"
    message: str = "Carrier status is required"


class SampleDoesNotExistError(CaseSampleError):
    field: str = "internal_id"
    message: str = "The sample does not exist"


class SexMissingError(CaseSampleError):
    field: str = "sex"
    message: str = "Sex is required"


class SourceMissingError(CaseSampleError):
    field: str = "source"
    message: str = "Source is required"


class SubjectIdSameAsCaseNameError(CaseSampleError):
    field: str = "subject_id"
    message: str = "Subject id must be different from the case name"


class ConcentrationRequiredIfSkipRCError(CaseSampleError):
    field: str = "concentration_ng_ul"
    message: str = "Concentration is required when skipping reception control"


class SubjectIdSameAsSampleNameError(CaseSampleError):
    field: str = "subject_id"
    message: str = "Subject id must be different from the sample name"


class InvalidConcentrationIfSkipRCError(CaseSampleError):
    def __init__(self, case_index: int, sample_index: int, allowed_interval: tuple[float, float]):
        field: str = "concentration_ng_ul"
        message: str = (
            f"Concentration must be between {allowed_interval[0]} ng/μL and {allowed_interval[1]} ng/μL if reception control should be skipped"
        )
        super(CaseSampleError, self).__init__(
            case_index=case_index, sample_index=sample_index, field=field, message=message
        )


class WellPositionMissingError(CaseSampleError):
    field: str = "well_position"
    message: str = "Well position is required for well plates"


class ContainerNameMissingError(CaseSampleError):
    field: str = "container_name"
    message: str = "Container name is required for well plates"


class InvalidVolumeError(CaseSampleError):
    field: str = "volume"
    message: str = f"Volume must be between {MINIMUM_VOLUME}-{MAXIMUM_VOLUME} μL"


class InvalidBufferError(CaseSampleError):
    field: str = "elution_buffer"
    message: str = "The chosen buffer is not allowed when skipping reception control"