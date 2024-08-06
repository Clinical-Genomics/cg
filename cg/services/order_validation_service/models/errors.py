from pydantic import BaseModel


class OrderError(BaseModel):
    field: str
    message: str


class CaseError(OrderError):
    case_name: str


class SampleError(OrderError):
    sample_name: str


class CaseSampleError(CaseError, SampleError):
    pass


class ValidationErrors(BaseModel):
    order_errors: list[OrderError] | None = None
    case_errors: list[CaseError] | None = None
    sample_errors: list[SampleError] | None = None
    case_sample_errors: list[CaseSampleError] | None = None


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
    def __init__(self, case_name: str, panels: list[str]):
        message = "Invalid panels: " + ",".join(panels)
        super(CaseError, self).__init__(field="panels", case_name=case_name, message=message)


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


class WellPositionMissingError(CaseSampleError):
    field: str = "well_position"
    message: str = "Well position is required for well plates"
