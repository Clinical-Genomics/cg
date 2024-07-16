from pydantic import BaseModel


class ValidationError(BaseModel):
    field: str
    message: str


class CaseError(ValidationError):
    case_id: str


class SampleError(ValidationError):
    sample_id: str


class CaseSampleError(ValidationError):
    sample_id: str
    case_id: str


class ValidationErrors(BaseModel):
    order_errors: list[ValidationError] | None = None
    case_errors: list[CaseError] | None = None
    sample_errors: list[SampleError] | None = None
    case_sample_errors: list[CaseSampleError] | None = None


class UserNotAssociatedWithCustomerError(ValidationError):
    field: str = "customer"
    message: str = "User does not belong to customer"


class TicketNumberRequiredError(ValidationError):
    field: str = "ticket_number"
    message: str = "Ticket number is required"


class CustomerCannotSkipReceptionControlError(ValidationError):
    field: str = "skip_reception_control"
    message: str = "Customer cannot skip reception control"


class CustomerDoesNotExistError(ValidationError):
    field: str = "customer"
    message: str = "Customer does not exist"


class OrderNameRequiredError(ValidationError):
    field: str = "name"
    message: str = "Order name is required"


class OccupiedWellError(CaseSampleError):
    message: str = "Well is already occupied"
