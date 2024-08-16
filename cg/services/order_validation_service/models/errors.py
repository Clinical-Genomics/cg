from pydantic import BaseModel

from cg.services.order_validation_service.constants import (
    MAXIMUM_VOLUME,
    MINIMUM_VOLUME,
)


class OrderError(BaseModel):
    field: str
    message: str


class CaseError(OrderError):
    case_index: int


class SampleError(OrderError):
    sample_index: int


class CaseSampleError(CaseError, SampleError):
    pass


class ValidationErrors(BaseModel):
    order_errors: list[OrderError] = []
    case_errors: list[CaseError] = []
    sample_errors: list[SampleError] = []
    case_sample_errors: list[CaseSampleError] = []


class UserNotAssociatedWithCustomerError(OrderError):
    field: str = "customer"
    message: str = "User does not belong to customer"


class TicketNumberRequiredError(OrderError):
    field: str = "ticket_number"
    message: str = "Ticket number is required"


class CustomerCannotSkipReceptionControlError(OrderError):
    field: str = "skip_reception_control"
    message: str = "Customer cannot skip reception control"


class CustomerDoesNotExistError(OrderError):
    field: str = "customer"
    message: str = "Customer does not exist"


class OrderNameRequiredError(OrderError):
    field: str = "name"
    message: str = "Order name is required"


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


class RepeatedCaseNameError(CaseError):
    field: str = "name"
    message: str = "Case name already used"


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


class InvalidGenePanelsError(CaseError):
    def __init__(self, case_index: int, panels: list[str]):
        message = "Invalid panels: " + ",".join(panels)
        super(CaseError, self).__init__(field="panels", case_index=case_index, message=message)


class InvalidBufferError(CaseSampleError):
    field: str = "elution_buffer"
    message: str = "The chosen buffer is not allowed when skipping reception control"


class RepeatedGenePanelsError(CaseError):
    field: str = "panels"
    message: str = "Gene panels must be unique"


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


class CaseNameNotAvailableError(CaseError):
    field: str = "name"
    message: str = "Case name already used in a previous order"


class CaseDoesNotExistError(CaseError):
    field: str = "internal_id"
    message: str = "The case does not exist"


class StatusMissingError(CaseSampleError):
    field: str = "status"
    message: str = "Carrier status is required"


class SampleDoesNotExistError(CaseSampleError):
    field: str = "internal_id"
    message: str = "The sample does not exist"


class SexMissingError(CaseSampleError):
    field: str = "sex"
    message: str = "Sex is required"
