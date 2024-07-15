from pydantic import BaseModel


class ValidationError(BaseModel):
    field: str
    message: str


class UserNotAssociatedWithCustomerError(ValidationError):
    field: str = "customer"
    message: str = "User does not belong to customer"


class TicketNumberRequiredError(ValidationError):
    field: str = "ticket_number"
    message: str = "Ticket number is required"
